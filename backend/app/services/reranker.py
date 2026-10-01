# backend/backend/app/services/reranker.py
"""
Local Reranking Service - NO API costs!

Uses cross-encoder model to rerank retrieved chunks.
Cross-encoders are much better at relevance scoring than embeddings alone.

Flow:
1. ChromaDB returns 20 chunks (fast, but some may be irrelevant)
2. Cross-encoder scores each chunk against query (slower, but very accurate)
3. Return top 7 highest scored chunks to LLM

Cost: FREE (runs locally)
Speed: ~50 chunks/second on CPU
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LocalReranker:
    """
    Local reranking using cross-encoder model
    
    Why reranking helps:
    - Embeddings (ChromaDB) are good at broad semantic similarity
    - Cross-encoders are excellent at precise relevance scoring
    - Combining both gives best results: fast + accurate
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize cross-encoder model
        
        Args:
            model_name: HuggingFace model name (defaults to config)
        """
        if model_name is None:
            model_name = settings.RERANK_MODEL
        
        self.model = None
        self.model_name = model_name
        
        try:
            logger.info(f"Loading reranker model: {model_name}")
            self.model = CrossEncoder(model_name)
            logger.info(f"✅ Reranker loaded successfully: {model_name}")
            print(f"✅ Reranker loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}", extra={
                "model": model_name,
                "error": str(e),
                "event": "reranker_load_failed"
            })
            print(f"⚠️  WARNING: Reranker failed to load: {e}")
            print(f"   Reranking will be disabled. System will work but with lower quality.")
    
    def rerank(
        self,
        query: str,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        distances: List[float],
        ids: List[str],
        top_k: int = 7
    ) -> Dict[str, Any]:
        """
        Rerank chunks using cross-encoder
        
        Args:
            query: User's question
            chunks: Retrieved document chunks from ChromaDB
            metadatas: Chunk metadata
            distances: Original embedding distances from ChromaDB
            ids: Chunk IDs
            top_k: Number of top results to return after reranking
        
        Returns:
            Reranked results in same format as vector_store.search()
            {
                "documents": List[str],
                "metadatas": List[Dict],
                "distances": List[float],
                "ids": List[str],
                "rerank_scores": List[float]  # NEW: actual relevance scores
            }
        """
        if not self.model:
            logger.warning("Reranker not available, returning original results")
            # Return top_k of original results without reranking
            return {
                "documents": chunks[:top_k],
                "metadatas": metadatas[:top_k],
                "distances": distances[:top_k],
                "ids": ids[:top_k]
            }
        
        if len(chunks) == 0:
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
        
        logger.debug(f"Reranking {len(chunks)} chunks to top {top_k}")
        
        # Create pairs of (query, chunk) for cross-encoder scoring
        pairs = [(query, chunk) for chunk in chunks]
        
        # Score all pairs - this is the magic!
        # Cross-encoder looks at query and chunk together
        scores = self.model.predict(pairs)
        
        # Combine everything with scores
        scored_chunks = list(zip(scores, chunks, metadatas, distances, ids))
        
        # Sort by score (highest = most relevant)
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Take top K
        top_chunks = scored_chunks[:top_k]
        
        # Log the improvement
        if len(top_chunks) > 0:
            top_score = float(top_chunks[0][0])
            logger.info("Reranking completed", extra={
                "input_chunks": len(chunks),
                "output_chunks": len(top_chunks),
                "top_score": top_score,
                "model": self.model_name,
                "event": "reranking_complete"
            })
        
        # Return in expected format
        return {
            "documents": [chunk for _, chunk, _, _, _ in top_chunks],
            "metadatas": [meta for _, _, meta, _, _ in top_chunks],
            "distances": [dist for _, _, _, dist, _ in top_chunks],
            "ids": [id_ for _, _, _, _, id_ in top_chunks],
            "rerank_scores": [float(score) for score, _, _, _, _ in top_chunks]
        }
    
    def is_available(self) -> bool:
        """Check if reranker is loaded and ready"""
        return self.model is not None


# Create singleton instance
local_reranker = LocalReranker()