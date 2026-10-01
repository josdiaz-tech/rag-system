# backend/backend/app/api/query.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.logging_config import get_logger, get_query_logger, get_cost_logger
from app.core.rate_limiter import limiter
from app.models.database import User, Query as QueryModel
from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_pipeline import rag_pipeline
from app.services.model_manager import model_manager  # NEW import
from datetime import datetime

router = APIRouter(prefix="/query", tags=["Query"])
logger = get_logger(__name__)
query_logger = get_query_logger()
cost_logger = get_cost_logger()


@router.post("/", response_model=QueryResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_QUERY)
async def ask_question(
    request: Request,
    response: Response,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question about your uploaded documents
    
    **NEW: Supports dynamic model selection!**
    - Leave `override_model` empty to use your configured model (global/user setting)
    - Provide `override_model` to use a specific model for this query only
    
    **Rate limit:** Configurable via RATE_LIMIT_QUERY (default: 20/hour)
    
    **How to use:**
    
    1. **Basic query** (uses your configured model):
```json
       {
         "question": "¿Cómo instalar fibra óptica?"
       }
```
    
    2. **Query with specific model** (override):
```json
       {
         "question": "Explain the complete FTTH architecture",
         "override_model": "anthropic/claude-sonnet-4"
       }
```
    
    3. **Search specific documents**:
```json
       {
         "question": "What are the safety requirements?",
         "document_ids": ["550e8400-e29b-41d4-a716-446655440000"]
       }
```
    
    **Available models:** See GET /api/admin/models/presets
    
    **Your current model:** See GET /api/admin/models/current
    """
    # Validate question
    if not query_data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
    
    # NEW: Get model configuration
    model_config = model_manager.get_model_config(
        db=db,
        user_id=current_user.id,
        override_model=query_data.override_model
    )
    
    logger.info("Query received", extra={
        "user_id": current_user.id,
        "question_length": len(query_data.question),
        "document_ids": query_data.document_ids,
        "model_id": model_config["model_id"],  # NEW: Log model
        "model_source": model_config["source"],  # NEW: Log source
        "event": "query_received"
    })
    
    # Process query through RAG pipeline with model config
    result = await rag_pipeline.query_documents(
        db=db,
        user_id=current_user.id,
        question=query_data.question,
        document_ids=query_data.document_ids,
        model_config=model_config  # NEW: Pass model config
    )
    
    # Check if there was an error
    if result["answer"].startswith("ERROR:"):
        logger.error("Query processing failed", extra={
            "user_id": current_user.id,
            "error": result["answer"],
            "event": "query_failed"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["answer"]
        )
    
    # Log successful query
    query_logger.info("Query completed", extra={
        "user_id": current_user.id,
        "query_id": result.get("id"),
        "chunks_retrieved": result["chunks_retrieved"],
        "response_time": result["response_time"],
        "model_used": result.get("model_used"),  # NEW
        "event": "query_completed"
    })
    
    # Log cost tracking
    if result.get("cost_usd"):
        cost_logger.info("API cost incurred", extra={
            "user_id": current_user.id,
            "query_id": result.get("id"),
            "tokens_used": result.get("tokens_used", 0),
            "cost_usd": result["cost_usd"],
            "model_used": result.get("model_used"),  # NEW
            "event": "api_cost"
        })
    
    return QueryResponse(
        id=result.get("id", 0),
        question=query_data.question,
        answer=result["answer"],
        sources=result["sources"],
        chunks_retrieved=result["chunks_retrieved"],
        response_time=result["response_time"],
        created_at=datetime.utcnow(),
        model_used=result.get("model_used"),  # NEW
        model_source=result.get("config_source")  # NEW
    )


@router.get("/history", response_model=List[QueryResponse])
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_query_history(
    request: Request,
    response: Response,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get query history for current user
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    
    Returns your recent questions and answers, ordered by most recent first.
    
    **Parameters:**
    - `limit`: Number of results to return (default: 20)
    - `offset`: Skip this many results (for pagination, default: 0)
    
    **Example:**
    - First page: limit=20, offset=0
    - Second page: limit=20, offset=20
    - Third page: limit=20, offset=40
    """
    queries = db.query(QueryModel).filter(
        QueryModel.user_id == current_user.id
    ).order_by(
        QueryModel.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    # Format response
    result = []
    for query in queries:
        result.append(QueryResponse(
            id=query.id,
            question=query.question,
            answer=query.answer,
            sources=[],  # Not storing sources in DB for now
            chunks_retrieved=query.chunks_retrieved or 0,
            response_time=query.response_time or 0.0,
            created_at=query.created_at,
            model_used=query.model_used,  # NEW: Show which model was used
            model_source=None  # Not stored in old queries
        ))
    
    return result