# backend/backend/app/api/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.rate_limiter import limiter
from app.models.database import User, Document
from app.models.schemas import DocumentResponse, DocumentStatus
from app.services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger(__name__)

async def process_document_background(
    document_id: str,
    file_path: str,
    user_id: int
):
    """
    Background task to initiate document processing in separate thread
    
    Note: This is called by FastAPI's BackgroundTasks, but it immediately
    spawns a new thread and returns, so it doesn't block the event loop.
    """
    from app.core.database import SessionLocal
    
    # Create a new database session for this thread
    db = SessionLocal()
    
    try:
        # Start processing in separate thread (non-blocking)
        rag_pipeline.process_document_async(
            db=db,
            document_id=document_id,
            file_path=file_path,
            user_id=user_id
        )
    except Exception as e:
        logger.error("Failed to start document processing thread", extra={
            "document_id": document_id,
            "user_id": user_id,
            "error": str(e),
            "event": "thread_start_failed"
        })
        db.close()
    # Note: db session will be closed by the thread when it completes


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: settings.RATE_LIMIT_UPLOAD)
async def upload_document(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document for processing
    
    **Rate limit:** Configurable via RATE_LIMIT_UPLOAD (default: 5/hour)
    
    **CONCURRENCY NOTE:**
    This endpoint now uses threading for document processing, which allows
    the server to handle other requests (queries, uploads) while a document
    is being processed with Vision API in the background.
    
    **Process:**
    1. Validates file type (PDF only) and size (max 50MB)
    2. Saves file securely with UUID filename
    3. Creates database record with status="processing"
    4. Returns immediately to user (non-blocking)
    5. Processes document in separate thread (Vision API calls don't block)
    6. Other API requests can be served concurrently
    """
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file
    is_valid, error_msg = rag_pipeline.doc_processor.validate_file(
        filename=file.filename,
        file_size=file_size
    )
    
    if not is_valid:
        logger.warning("Document upload validation failed", extra={
            "user_id": current_user.id,
            "uploaded_filename": file.filename,
            "file_size": file_size,
            "error": error_msg,
            "event": "upload_validation_failed"
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Generate safe filename (UUID-based, prevents path traversal)
    safe_filename = rag_pipeline.doc_processor.generate_safe_filename(file.filename)
    
    # Save file to disk
    file_path = rag_pipeline.doc_processor.save_file(content, safe_filename)
    
    # Calculate file hash (for deduplication detection)
    file_hash = rag_pipeline.doc_processor.calculate_file_hash(file_path)
    
    # Create document record in database
    document = rag_pipeline.doc_processor.create_document_record(
        db=db,
        user_id=current_user.id,
        original_filename=file.filename,
        safe_filename=safe_filename,
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash
    )
    
    logger.info("Document uploaded successfully", extra={
        "user_id": current_user.id,
        "document_id": document.id,
        "uploaded_filename": file.filename,
        "file_size": file_size,
        "event": "document_uploaded"
    })
    
    # Process document in background thread (truly non-blocking)
    background_tasks.add_task(
        process_document_background,
        document.id,
        file_path,
        current_user.id
    )
    
    return document
@router.get("/", response_model=List[DocumentResponse])
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def list_documents(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all documents for current user
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    
    Why this limit?
    - Lightweight database query
    - No expensive processing
    - Higher limit is fine for this endpoint
    
    **Returns:**
    - Array of all documents uploaded by current user
    - Ordered by most recent first
    - Includes processing status, page count, chunk count
    - Only sees own documents (user isolation enforced)
    """
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_document(
    request: Request,
    response: Response,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get document details
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    
    Why this limit?
    - Simple database lookup
    - No processing involved
    - Higher limit appropriate
    
    **Security:**
    - Verifies document ownership (user_id match)
    - Returns 404 if not found or not yours
    - Cannot access other users' documents
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.get("/{document_id}/status", response_model=DocumentStatus)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_document_status(
    request: Request,
    response: Response,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check document processing status
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    
    Why this limit?
    - Frontend may poll this endpoint frequently
    - Very lightweight query
    - High limit allows real-time status updates
    
    **Status values:**
    - "processing": Document being processed in background
    - "ready": Document ready for queries
    - "failed": Processing failed (see error_message)
    
    **Use case:**
    Frontend can poll this endpoint every 2-3 seconds after upload
    to show progress to user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentStatus(
        id=document.id,
        status=document.status,
        error_message=document.error_message
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def delete_document(
    request: Request,
    response: Response,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its chunks from vector store
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    
    Why this limit?
    - Involves multiple operations (DB, vector store, file system)
    - Not as expensive as upload/query
    - General limit is appropriate
    
    **Process:**
    1. Verifies document ownership
    2. Deletes chunks from vector store (ChromaDB)
    3. Deletes physical PDF file from disk
    4. Deletes database record
    
    **Security:**
    - Only owner can delete
    - All related data cleaned up (no orphaned data)
    
    **Note:**
    Deletion is permanent and cannot be undone.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from vector store (removes all chunks)
    from app.services.vector_store import vector_store_service
    vector_store_service.delete_document_chunks(document_id, current_user.id)
    
    # Delete file from disk
    import os
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            logger.error("Failed to delete file from disk", extra={
                "document_id": document_id,
                "file_path": document.file_path,
                "error": str(e),
                "event": "file_deletion_failed"
            })
    
    logger.info("Document deleted", extra={
        "user_id": current_user.id,
        "document_id": document_id,
        "deleted_filename": document.original_filename,
        "event": "document_deleted"
    })
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return None

@router.get("/processing-status", response_model=Dict[str, Any])
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_processing_status(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current document processing status
    
    Returns count of documents currently being processed in background threadss
    """
    return {
        "active_processing_count": rag_pipeline.get_active_processing_count()
    }
