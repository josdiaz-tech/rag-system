# backend/backend/app/services/rag_pipeline.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.services.document_processor import DocumentProcessor
from app.services.text_chunker import text_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service
from app.services.llm_service import llm_service
from app.models.database import Document, Query
from app.core.logging_config import get_logger
from app.core.config import settings
from app.services.hyde_retriever import hyde_retriever
import time
import threading

logger = get_logger(__name__)


class RAGPipeline:
    """
    Orchestrates the RAG pipeline:
    1. Document processing (upload → extract → chunk → embed → store)
    2. Query processing (question → embed → search → generate answer)
    """
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self._processing_threads = {}  # Track active threads
        print("✅ RAG Pipeline initialized")
    
    def process_document_async(
        self,
        db: Session,
        document_id: str,
        file_path: str,
        user_id: int
    ):
        """
        Start document processing in a separate thread
        
        This allows the FastAPI server to continue serving other requests
        while document processing (especially Vision API calls) happens
        in the background.
        """
        # Create a new thread for processing
        thread = threading.Thread(
            target=self._process_document_sync,
            args=(db, document_id, file_path, user_id),
            daemon=True,
            name=f"doc_processor_{document_id}"
        )
        
        # Track the thread
        self._processing_threads[document_id] = thread
        
        # Start processing
        thread.start()
        
        logger.info("Document processing started in background thread", extra={
            "document_id": document_id,
            "user_id": user_id,
            "thread_name": thread.name,
            "event": "document_processing_started"
        })
        
        return thread
    
    def _process_document_sync(
        self,
        db: Session,
        document_id: str,
        file_path: str,
        user_id: int
    ):
        """
        Synchronous document processing (runs in separate thread)
        
        Complete document processing pipeline:
        1. Extract text from PDF (with Vision API)
        2. Sanitize text
        3. Chunk text
        4. Generate embeddings
        5. Store in vector database
        6. Update document status
        """
        try:
            logger.info("Starting document processing", extra={
                "document_id": document_id,
                "user_id": user_id,
                "event": "document_processing_start"
            })
            
            # Step 1: Extract text from PDF (with Vision API)
            logger.debug("Extracting text from PDF", extra={
                "document_id": document_id,
                "event": "pdf_extraction_start"
            })
            
            text_content, page_count = self.doc_processor.extract_text_from_pdf(
                file_path=file_path,
                use_vision=True
            )
            
            if not text_content or len(text_content.strip()) < 50:
                raise Exception("Failed to extract meaningful text from PDF")
            
            logger.info("Text extraction completed", extra={
                "document_id": document_id,
                "page_count": page_count,
                "text_length": len(text_content),
                "event": "pdf_extraction_complete"
            })
            
            # Step 2: Sanitize text
            text_content = self.doc_processor.sanitize_text(text_content)
            
            # Step 3: Chunk text
            logger.debug("Chunking text", extra={
                "document_id": document_id,
                "event": "chunking_start"
            })
            
            chunk_texts, metadatas = text_chunker.chunk_text_with_metadata(
                text=text_content,
                document_id=document_id,
                user_id=user_id,
                source_file=document_id
            )
            
            logger.info("Text chunking completed", extra={
                "document_id": document_id,
                "chunk_count": len(chunk_texts),
                "event": "chunking_complete"
            })
            
            # Step 4: Generate embeddings
            logger.debug("Generating embeddings", extra={
                "document_id": document_id,
                "chunk_count": len(chunk_texts),
                "event": "embedding_start"
            })
            
            embeddings = embedding_service.encode_texts(chunk_texts)
            
            logger.info("Embeddings generated", extra={
                "document_id": document_id,
                "embedding_count": len(embeddings),
                "event": "embedding_complete"
            })
            
            # Step 5: Store in vector database
            logger.debug("Storing in vector database", extra={
                "document_id": document_id,
                "event": "vector_store_start"
            })
            
            chunk_ids = [f"{document_id}_{i}" for i in range(len(chunk_texts))]
            
            vector_store_service.add_chunks(
                chunks=chunk_texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info("Vector storage completed", extra={
                "document_id": document_id,
                "event": "vector_store_complete"
            })
            
            # Step 6: Update document status
            self.doc_processor.update_document_status(
                db=db,
                document_id=document_id,
                status="ready",
                page_count=page_count,
                chunk_count=len(chunk_texts)
            )
            
            logger.info("Document processing completed successfully", extra={
                "document_id": document_id,
                "user_id": user_id,
                "page_count": page_count,
                "chunk_count": len(chunk_texts),
                "event": "document_processing_complete"
            })
        
        except Exception as e:
            logger.error("Document processing failed", extra={
                "document_id": document_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "event": "document_processing_failed"
            })
            
            # Update document status to failed
            try:
                self.doc_processor.update_document_status(
                    db=db,
                    document_id=document_id,
                    status="failed",
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error("Failed to update document status", extra={
                    "document_id": document_id,
                    "error": str(db_error),
                    "event": "status_update_failed"
                })
        
        finally:
            # Clean up thread tracking
            if document_id in self._processing_threads:
                del self._processing_threads[document_id]
    
    def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """Check if a document is currently being processed"""
        thread = self._processing_threads.get(document_id)
        if thread:
            return {
                "is_processing": thread.is_alive(),
                "thread_name": thread.name
            }
        return {"is_processing": False}
    
    def get_active_processing_count(self) -> int:
        """Get count of currently processing documents"""
        return sum(1 for t in self._processing_threads.values() if t.is_alive())
    
    async def query_documents(
        self,
        db: Session,
        user_id: int,
        question: str,
        document_ids: Optional[List[str]] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query documents and generate answer
        
        NEW: Supports reranking for better chunk selection
        
        Args:
            db: Database session
            user_id: User ID (for filtering)
            question: User's question
            document_ids: Optional list of document IDs to search
            model_config: Optional model configuration from ModelManager
        
        Returns:
            {
                "answer": str,
                "sources": list,
                "chunks_retrieved": int,
                "tokens_used": int,
                "cost_usd": float,
                "response_time": float,
                "model_used": str,
                "config_source": str,
                "retrieval_method": str
            }
        """
        start_time = time.time()
        
        try:
            logger.debug("Starting query", extra={
                "user_id": user_id,
                "question_length": len(question),
                "document_ids": document_ids,
                "reranking_enabled": settings.ENABLE_RERANKING,
                "event": "query_start"
            })
            
            # === RETRIEVAL WITH OPTIONAL RERANKING ===
            if settings.ENABLE_RERANKING:
                from app.services.reranker import local_reranker
                
                # Step 1: Retrieve MORE chunks from ChromaDB (fast but less precise)
                initial_k = settings.RERANK_INITIAL_K
                
                logger.debug(f"Retrieving {initial_k} chunks for reranking", extra={
                    "initial_k": initial_k,
                    "event": "retrieval_start"
                })
                
                question_embedding = embedding_service.encode_text(question)
                initial_results = vector_store_service.search(
                    query_embedding=question_embedding,
                    user_id=user_id,
                    document_ids=document_ids,
                    top_k=initial_k
                )
                
                if not initial_results["documents"]:
                    logger.info("No results from initial retrieval", extra={
                        "user_id": user_id,
                        "event": "no_results"
                    })
                    
                    return {
                        "answer": "No encontré información relevante en tus documentos para responder esta pregunta.",
                        "sources": [],
                        "chunks_retrieved": 0,
                        "tokens_used": 0,
                        "cost_usd": 0.0,
                        "response_time": time.time() - start_time,
                        "model_used": model_config.get("model_id") if model_config else "none",
                        "config_source": model_config.get("source") if model_config else "none",
                        "retrieval_method": "none"
                    }
                
                # Step 2: Rerank with cross-encoder (slower but very precise)
                search_results = local_reranker.rerank(
                    query=question,
                    chunks=initial_results["documents"],
                    metadatas=initial_results["metadatas"],
                    distances=initial_results["distances"],
                    ids=initial_results["ids"],
                    top_k=settings.RERANK_FINAL_K
                )
                
                retrieval_method = "reranked"
                
                logger.info("Used reranking", extra={
                    "initial_chunks": len(initial_results["documents"]),
                    "final_chunks": len(search_results["documents"]),
                    "top_rerank_score": search_results.get("rerank_scores", [0])[0] if search_results.get("rerank_scores") else 0,
                    "event": "reranking_used"
                })
            
            elif settings.ENABLE_HYDE and settings.HYDE_FALLBACK_MODE:
                # HyDE with smart fallback
                search_results, retrieval_method = await hyde_retriever.retrieve_with_smart_fallback(
                    question=question,
                    embedding_service=embedding_service,
                    vector_store_service=vector_store_service,
                    user_id=user_id,
                    document_ids=document_ids,
                    top_k=settings.TOP_K_RESULTS
                )
            
            elif settings.ENABLE_HYDE and not settings.HYDE_FALLBACK_MODE:
                # Always use HyDE
                search_results = await hyde_retriever.retrieve_with_hyde(
                    question=question,
                    embedding_service=embedding_service,
                    vector_store_service=vector_store_service,
                    user_id=user_id,
                    document_ids=document_ids,
                    top_k=settings.TOP_K_RESULTS
                )
                retrieval_method = "hyde"
            
            else:
                # Standard retrieval (default)
                question_embedding = embedding_service.encode_text(question)
                search_results = vector_store_service.search(
                    query_embedding=question_embedding,
                    user_id=user_id,
                    document_ids=document_ids,
                    top_k=settings.TOP_K_RESULTS
                )
                retrieval_method = "standard"
            
            # === REST OF THE CODE IS THE SAME ===
            
            if not search_results["documents"]:
                logger.info("No relevant documents found", extra={
                    "user_id": user_id,
                    "question": question[:100],
                    "retrieval_method": retrieval_method,
                    "event": "query_no_results"
                })
                
                return {
                    "answer": "No encontré información relevante en tus documentos para responder esta pregunta.",
                    "sources": [],
                    "chunks_retrieved": 0,
                    "tokens_used": 0,
                    "cost_usd": 0.0,
                    "response_time": time.time() - start_time,
                    "model_used": model_config.get("model_id") if model_config else "none",
                    "config_source": model_config.get("source") if model_config else "none",
                    "retrieval_method": retrieval_method
                }
            
            # 3. Prepare context chunks
            chunk_texts = search_results["documents"]
            
            # 4. Generate answer with LLM
            if model_config:
                llm_result = await llm_service.generate_answer_with_config(
                    question=question,
                    context_chunks=chunk_texts,
                    model_config=model_config
                )
            else:
                llm_result = await llm_service.generate_answer(
                    question=question,
                    context_chunks=chunk_texts
                )
            
            # 5. Format sources
            sources = []
            for i, (doc, meta) in enumerate(zip(search_results["documents"], search_results["metadatas"])):
                source_info = {
                    "document_id": meta.get("document_id"),
                    "source_file": meta.get("source_file"),
                    "chunk_index": meta.get("chunk_index", i),
                    "chunk_text": doc[:200] + "..." if len(doc) > 200 else doc
                }
                
                # Add rerank score if available
                if "rerank_scores" in search_results and i < len(search_results["rerank_scores"]):
                    source_info["relevance_score"] = search_results["rerank_scores"][i]
                
                sources.append(source_info)
            
            response_time = time.time() - start_time
            
            # 6. Save query to database
            db_query = Query(
                question=question,
                answer=llm_result["answer"],
                document_ids=",".join(document_ids) if document_ids else "",
                chunks_retrieved=len(search_results["documents"]),
                provider="openrouter",
                model_used=llm_result.get("model"),
                tokens_used=llm_result.get("tokens_used", 0),
                cost_usd=llm_result.get("cost_usd", 0.0),
                model_cost_actual=llm_result.get("cost_usd", 0.0),
                response_time=response_time,
                user_id=user_id
            )
            
            db.add(db_query)
            db.commit()
            db.refresh(db_query)
            
            logger.info("Query completed successfully", extra={
                "user_id": user_id,
                "query_id": db_query.id,
                "response_time": response_time,
                "chunks_retrieved": len(search_results["documents"]),
                "tokens_used": llm_result.get("tokens_used", 0),
                "cost_usd": llm_result.get("cost_usd", 0.0),
                "retrieval_method": retrieval_method,
                "event": "query_complete"
            })
            
            return {
                "id": db_query.id,
                "answer": llm_result["answer"],
                "sources": sources,
                "chunks_retrieved": len(search_results["documents"]),
                "tokens_used": llm_result.get("tokens_used", 0),
                "cost_usd": llm_result.get("cost_usd", 0.0),
                "response_time": response_time,
                "model_used": llm_result.get("model"),
                "config_source": llm_result.get("config_source", "default"),
                "retrieval_method": retrieval_method
            }
        
        except Exception as e:
            logger.error("Query processing error", extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "event": "query_error"
            })
            
            return {
                "answer": f"ERROR: {str(e)}",
                "sources": [],
                "chunks_retrieved": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "response_time": time.time() - start_time,
                "model_used": "error",
                "config_source": "error",
                "retrieval_method": "error"
            }

# Create singleton instance
rag_pipeline = RAGPipeline()