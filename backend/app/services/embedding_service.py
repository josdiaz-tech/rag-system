from sentence_transformers import SentenceTransformer
from typing import List
import torch
from app.core.config import settings


class EmbeddingService:
    """
    Local embedding service using sentence-transformers
    FREE - No API costs!
    """
    
    def __init__(self):
        print(f"🔄 Loading embedding model: {settings.EMBEDDING_MODEL}")
        
        # Use CPU or GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"📍 Using device: {self.device}")
        
        # Load model
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL, device=self.device)
        print(f"✅ Embedding model loaded successfully!")
    
    def encode_text(self, text: str) -> List[float]:
        """
        Encode a single text into embedding vector
        Returns: List of floats (embedding vector)
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Encode multiple texts into embedding vectors (batch processing)
        Returns: List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self.model.get_sentence_embedding_dimension()


# Create singleton instance
embedding_service = EmbeddingService()
