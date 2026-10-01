# backend/backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./rag.db"
    
    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "anthropic/claude-sonnet-4"
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "../uploads"
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]
    
    # Vector Database
    CHROMA_PERSIST_DIR: str = "../chroma_db"
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # === NEW: Reranking Configuration ===
    ENABLE_RERANKING: bool = True  # Master switch for reranking
    RERANK_INITIAL_K: int = 20     # How many chunks to retrieve from ChromaDB
    RERANK_FINAL_K: int = 7        # How many chunks to pass to LLM after reranking
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Cross-encoder model
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_DIR: str = "../../logs"
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH: str = "10/hour"
    RATE_LIMIT_UPLOAD: str = "5/hour"
    RATE_LIMIT_QUERY: str = "20/hour"
    RATE_LIMIT_GENERAL: str = "100/hour"
    RATE_LIMIT_EXEMPT_IPS: List[str] = []
    
    # Application
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "RAG Document Q&A System"
    DEBUG: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]

    # Admin configuration
    ADMIN_EMAILS: str = ""
    
    def get_admin_emails(self) -> list[str]:
        """Parse admin emails from comma-separated string"""
        if not self.ADMIN_EMAILS:
            return []
        return [email.strip().lower() for email in self.ADMIN_EMAILS.split(",")]
    
    # HyDE Configuration (optional feature)
    ENABLE_HYDE: bool = False
    HYDE_MODEL: str = "google/gemini-flash-1.5"
    HYDE_MIN_RESULTS_THRESHOLD: int = 3
    HYDE_FALLBACK_MODE: bool = True
    HYDE_MAX_TOKENS: int = 600
    HYDE_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Resolve LOG_DIR to absolute path
if not os.path.isabs(settings.LOG_DIR):
    settings.LOG_DIR = str(Path(__file__).parent.parent / settings.LOG_DIR)

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

try:
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    print(f"✅ Logs directory: {os.path.abspath(settings.LOG_DIR)}")
except Exception as e:
    print(f"❌ ERROR creating logs directory: {e}")
    print(f"   Attempted path: {settings.LOG_DIR}")