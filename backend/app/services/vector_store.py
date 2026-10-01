# app/services/vector_store.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.core.config import settings


class VectorStoreService:
    """
    Vector database service using ChromaDB
    Stores document chunks with embeddings for similarity search
    """
    
    def __init__(self):
        print(f"🔄 Initializing ChromaDB at: {settings.CHROMA_PERSIST_DIR}")
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document chunks with embeddings"}
        )
        
        print(f"✅ ChromaDB initialized! Collection has {self.collection.count()} chunks")
    
    def add_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add document chunks to vector store
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts (must include user_id!)
            ids: List of unique IDs for each chunk
        """
        # CRITICAL: Ensure all metadata has user_id for filtering
        for metadata in metadatas:
            if "user_id" not in metadata:
                raise ValueError("Metadata must include user_id for multi-user isolation!")
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Added {len(chunks)} chunks to vector store")
    
    def search(
        self,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 5,
        document_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Search for similar chunks
        
        CRITICAL: Always filters by user_id for security!
        
        Args:
            query_embedding: Query vector
            user_id: User ID for filtering (REQUIRED)
            top_k: Number of results to return
            document_ids: Optional list of document IDs to filter by
        
        Returns:
            Dict with 'documents', 'metadatas', 'distances', 'ids'
        """
        # Build where filter - ALWAYS include user_id
        # When we have both user_id and document_ids, use $and operator
        if document_ids:
            where_filter = {
                "$and": [
                    {"user_id": user_id},
                    {"document_id": {"$in": document_ids}}
                ]
            }
        else:
            # Simple filter when only user_id
            where_filter = {"user_id": user_id}
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    def delete_document_chunks(self, document_id: str, user_id: int):
        """
        Delete all chunks for a specific document
        Includes user_id check for security
        """
        # Get all chunk IDs for this document and user
        results = self.collection.get(
            where={
                "$and": [
                    {"document_id": document_id},
                    {"user_id": user_id}
                ]
            }
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            print(f"✅ Deleted {len(results['ids'])} chunks for document {document_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection.name
        }


# Create singleton instance
vector_store_service = VectorStoreService()