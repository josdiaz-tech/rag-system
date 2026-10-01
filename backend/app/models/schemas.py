# backend/backend/app/models/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# Document Schemas
class DocumentUpload(BaseModel):
    pass  # File will be handled via UploadFile


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentStatus(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None


# Query Schemas
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    document_ids: Optional[List[str]] = None  # Optional: filter by specific documents
    # NEW: Optional model override (backward compatible - defaults to None)
    override_model: Optional[str] = Field(
        None, 
        description="Optional: Override model for this query only (e.g., 'anthropic/claude-sonnet-4')"
    )


class QueryResponse(BaseModel):
    id: int
    question: str
    answer: str
    sources: List[dict] = []  # List of source chunks with metadata
    chunks_retrieved: int
    response_time: float
    created_at: datetime
    # NEW: Show which model was used (optional for backward compatibility)
    model_used: Optional[str] = None
    model_source: Optional[str] = None  # 'default', 'global', 'user', 'query_override'
    
    class Config:
        from_attributes = True


class QueryHistory(BaseModel):
    queries: List[QueryResponse]
    total: int
    page: int
    page_size: int