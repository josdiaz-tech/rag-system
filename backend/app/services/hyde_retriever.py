# backend/backend/app/services/hyde_retriever.py
"""
HyDE (Hypothetical Document Embeddings) Retriever

Solves the "semantic gap" problem in RAG:
- User asks: "¿Cuál es la API?"
- Document says: "interfaz de servicio web"
- Standard search fails ❌
- HyDE generates hypothetical document with varied vocabulary ✅

This is a STANDALONE module that doesn't modify existing code.
"""

import httpx
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class HyDERetriever:
    """
    Hypothetical Document Embeddings (HyDE) for improved retrieval
    
    How it works:
    1. User asks: "¿Cuál es la API?"
    2. LLM generates hypothetical doc: "El sistema tiene una API REST que 
       proporciona una interfaz web para desarrolladores..."
    3. Embed the hypothetical doc (not the query)
    4. Search vector store with this richer embedding
    5. Find: "interfaz web" ✅
    
    IMPORTANT: This is an OPTIONAL enhancement. Your system works fine without it.
    """
    
    def __init__(self):
        """Initialize HyDE retriever with LLM connection"""
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.HYDE_MODEL
        self.max_tokens = settings.HYDE_MAX_TOKENS
        self.temperature = settings.HYDE_TEMPERATURE
        
        if not self.api_key:
            logger.warning("HyDE: OpenRouter API key not configured")
        else:
            logger.info(f"HyDE Retriever initialized with model: {self.model}")
    
    async def generate_hypothetical_document(
        self,
        question: str,
        language: str = "es"
    ) -> str:
        """
        Generate hypothetical document that COULD answer the question
        
        IMPORTANT: The document doesn't need to be factually correct!
        It just needs to use varied technical vocabulary to improve matching.
        
        Args:
            question: User's question
            language: Language for document (default: Spanish)
        
        Returns:
            Hypothetical document text (or original question if generation fails)
        """
        if not self.api_key:
            logger.warning("HyDE: Cannot generate hypothetical doc - no API key")
            return question  # Fallback to original question
        
        # Build prompt for hypothesis generation
        hyde_prompt = self._build_hypothesis_prompt(question, language)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at generating technical documentation excerpts."
                            },
                            {
                                "role": "user",
                                "content": hyde_prompt
                            }
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                hypothetical_doc = data["choices"][0]["message"]["content"]
                
                logger.info("HyDE: Generated hypothetical document", extra={
                    "question_length": len(question),
                    "doc_length": len(hypothetical_doc),
                    "model": self.model,
                    "event": "hyde_generation_success"
                })
                
                logger.debug(f"HyDE document preview: {hypothetical_doc[:200]}...")
                
                return hypothetical_doc
        
        except Exception as e:
            logger.error("HyDE: Failed to generate hypothetical document", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "event": "hyde_generation_failed"
            })
            # Fallback: return original question
            return question
    
    def _build_hypothesis_prompt(self, question: str, language: str) -> str:
        """Build prompt for generating hypothetical document"""
        
        if language == "es":
            return f"""Eres un experto en documentación técnica de telecomunicaciones FTTH.

Tu tarea: Genera un extracto de manual técnico de aproximadamente 300 palabras que PODRÍA contener la respuesta a esta pregunta.

REGLAS CRÍTICAS:
1. NO inventes datos específicos (URLs, IPs, números de modelo, nombres propios)
2. USA vocabulario técnico VARIADO y sinónimos
3. Incluye términos formales Y coloquiales del mismo concepto
4. Escribe como si fuera parte de un manual profesional
5. Si la pregunta menciona "API", incluye también: "interfaz web", "servicio web", "endpoint", "REST"
6. Si menciona términos técnicos, incluye sus variaciones

Pregunta del usuario: {question}

Extracto de manual técnico (usa vocabulario variado):"""
        else:
            return f"""You are an expert in FTTH telecommunications technical documentation.

Your task: Generate a ~300 word technical manual excerpt that COULD contain the answer to this question.

CRITICAL RULES:
1. Do NOT invent specific data (URLs, IPs, model numbers, proper names)
2. USE VARIED technical vocabulary and synonyms
3. Include both formal and colloquial terms for same concepts
4. Write as if from a professional manual
5. If question mentions "API", also include: "web interface", "web service", "endpoint", "REST"
6. If it mentions technical terms, include their variations

User question: {question}

Technical manual excerpt (use varied vocabulary):"""
    
    async def retrieve_with_hyde(
        self,
        question: str,
        embedding_service,  # Pass the service instance
        vector_store_service,  # Pass the service instance
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve documents using HyDE approach
        
        Args:
            question: User's question
            embedding_service: Instance of EmbeddingService
            vector_store_service: Instance of VectorStoreService
            user_id: User ID for filtering
            document_ids: Optional document IDs to search within
            top_k: Number of results to return
        
        Returns:
            {
                "documents": List[str],
                "metadatas": List[Dict],
                "distances": List[float],
                "method": "hyde"
            }
        """
        logger.info("HyDE: Starting retrieval", extra={
            "user_id": user_id,
            "question_length": len(question),
            "event": "hyde_retrieval_start"
        })
        
        # Step 1: Generate hypothetical document
        hypothetical_doc = await self.generate_hypothetical_document(question)
        
        # Step 2: Generate embedding of hypothetical document (NOT the query!)
        hyde_embedding = embedding_service.encode_text(hypothetical_doc)
        
        logger.debug("HyDE: Generated embedding for hypothetical document")
        
        # Step 3: Search vector store with hypothetical document embedding
        search_results = vector_store_service.search(
            query_embedding=hyde_embedding,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k
        )
        
        # Add method marker
        search_results["method"] = "hyde"
        
        logger.info("HyDE: Retrieval completed", extra={
            "user_id": user_id,
            "results_found": len(search_results.get("documents", [])),
            "event": "hyde_retrieval_complete"
        })
        
        return search_results
    
    async def retrieve_with_smart_fallback(
        self,
        question: str,
        embedding_service,
        vector_store_service,
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Tuple[Dict[str, Any], str]:
        """
        Smart retrieval with automatic fallback to HyDE
        
        Strategy:
        1. Try standard retrieval first
        2. If results < threshold, use HyDE
        3. Return best results + method used
        
        Args:
            (same as retrieve_with_hyde)
        
        Returns:
            (search_results, method_used)
            where method_used is "standard" or "hyde"
        """
        # Step 1: Try standard retrieval first
        query_embedding = embedding_service.encode_text(question)
        standard_results = vector_store_service.search(
            query_embedding=query_embedding,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k
        )
        
        num_standard_results = len(standard_results.get("documents", []))
        
        # Check if standard retrieval is sufficient
        if num_standard_results >= settings.HYDE_MIN_RESULTS_THRESHOLD:
            logger.info("HyDE: Standard retrieval sufficient, skipping HyDE", extra={
                "results_found": num_standard_results,
                "threshold": settings.HYDE_MIN_RESULTS_THRESHOLD,
                "event": "hyde_skipped"
            })
            standard_results["method"] = "standard"
            return standard_results, "standard"
        
        # Step 2: Standard retrieval insufficient, try HyDE
        logger.info("HyDE: Standard retrieval insufficient, trying HyDE", extra={
            "standard_results": num_standard_results,
            "threshold": settings.HYDE_MIN_RESULTS_THRESHOLD,
            "event": "hyde_fallback_triggered"
        })
        
        hyde_results = await self.retrieve_with_hyde(
            question=question,
            embedding_service=embedding_service,
            vector_store_service=vector_store_service,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k
        )
        
        num_hyde_results = len(hyde_results.get("documents", []))
        
        # Use HyDE results if better
        if num_hyde_results > num_standard_results:
            logger.info("HyDE: Using HyDE results (better than standard)", extra={
                "hyde_results": num_hyde_results,
                "standard_results": num_standard_results,
                "event": "hyde_results_used"
            })
            return hyde_results, "hyde"
        else:
            logger.info("HyDE: Using standard results (HyDE didn't improve)", extra={
                "hyde_results": num_hyde_results,
                "standard_results": num_standard_results,
                "event": "standard_results_used"
            })
            standard_results["method"] = "standard"
            return standard_results, "standard"
    
    def is_available(self) -> bool:
        """Check if HyDE is available (needs API key)"""
        return bool(self.api_key) and settings.ENABLE_HYDE


# Create singleton instance (but only used if ENABLE_HYDE=True)
hyde_retriever = HyDERetriever()