from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from app.core.config import settings


class TextChunker:
    """
    Split text into overlapping chunks for RAG
    Uses LangChain's RecursiveCharacterTextSplitter
    """
    
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        print(f"✅ Text chunker initialized (size={settings.CHUNK_SIZE}, overlap={settings.CHUNK_OVERLAP})")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Full document text
        
        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = self.splitter.split_text(text)
        
        print(f"📄 Created {len(chunks)} chunks from text")
        return chunks
    
    def chunk_text_with_metadata(
        self,
        text: str,
        document_id: str,
        user_id: int,
        source_file: str
    ) -> tuple[List[str], List[dict]]:
        """
        Split text and create metadata for each chunk
        
        Returns:
            (chunks, metadatas)
        """
        chunks = self.chunk_text(text)
        
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "user_id": user_id,  # CRITICAL for filtering
                "document_id": document_id,
                "chunk_index": i,
                "source_file": source_file,
                "chunk_length": len(chunk)
            }
            metadatas.append(metadata)
        
        return chunks, metadatas


# Create singleton instance
text_chunker = TextChunker()
