# backend/backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging, get_logger
from app.api import auth, documents, query, admin  # NEW: Import admin router

# Initialize logging (now outside watched directory)
setup_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)


# ============================================================================
# LIFESPAN CONTEXT MANAGER (Replaces deprecated @app.on_event)
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("=" * 50)
    print("🚀 Starting RAG Document Q&A System")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # NEW: Initialize model presets
    from app.utils.init_presets import initialize_default_presets
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        initialize_default_presets(db)
    finally:
        db.close()
    
    logger.info("System started successfully")
    
    print("=" * 50)
    print("✅ System ready!")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print(f"👨‍💼 Admin Panel: http://localhost:8000/docs#/Admin")  # NEW
    print(f"🛡️  Security: Request size limits + Security headers enabled")
    print("=" * 50)
    
    yield  # Application runs here
    
    # Shutdown
    print("👋 Shutting down RAG System...")
    logger.info("System shutdown")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="RAG-based Document Q&A System with Dynamic Model Management",  # Updated
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================================
# SECURITY MIDDLEWARE - Request Size Limits (JSON only)
# ============================================================================
@app.middleware("http")
async def limit_json_request_size(request: Request, call_next):
    """
    Limit JSON request body size to prevent DOS attacks
    
    - Only applies to application/json content type
    - Does NOT affect file uploads (multipart/form-data)
    - File uploads already limited by MAX_FILE_SIZE_MB (50MB)
    - JSON bodies limited to 1MB (more than enough for auth/queries)
    
    Why 1MB for JSON?
    - Login request: ~200 bytes
    - Register request: ~300 bytes  
    - Query request: ~5KB typical (long questions)
    - 1MB = 1000x more than needed, very safe buffer
    """
    content_type = request.headers.get("content-type", "")
    
    # Only check JSON requests (not multipart file uploads)
    if "application/json" in content_type.lower():
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            max_json_size = 1 * 1024 * 1024  # 1MB for JSON
            
            if content_length > max_json_size:
                logger.warning("Request body too large", extra={
                    "content_length": content_length,
                    "max_allowed": max_json_size,
                    "content_type": content_type,
                    "event": "request_size_exceeded"
                })
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Maximum size for JSON requests: {max_json_size/1024/1024}MB"
                    }
                )
    
    response = await call_next(request)
    return response


# ============================================================================
# SECURITY MIDDLEWARE - Security Headers (XSS Protection)
# ============================================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses
    
    Headers explained:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS filter
    - Content-Security-Policy: Controls resource loading (adjusted for Swagger UI)
    """
    response = await call_next(request)
    
    # Add basic security headers (always applied)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Content Security Policy - Permissive for documentation, strict for API
    path = request.url.path
    
    if path in ["/docs", "/redoc", "/openapi.json"]:
        # Permissive CSP for Swagger UI and ReDoc
        # Allows loading resources from CDN for documentation
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
    else:
        # Strict CSP for API endpoints (your actual application)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(query.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)  # NEW: Admin routes


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "RAG Document Q&A System",
        "version": "1.0.0",
        "docs": "/docs",
        "features": ["Dynamic Model Management", "Multi-User Support", "Cost Tracking"]  # NEW
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    from app.services.llm_service import llm_service
    from app.services.vector_store import vector_store_service
    
    return {
        "status": "healthy",
        "llm_available": llm_service.is_available(),
        "vector_store_chunks": vector_store_service.get_stats()["total_chunks"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )