# backend/backend/app/models/database.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    # NEW: Relationship to model settings
    model_settings = relationship(
        "ModelSetting", 
        foreign_keys="[ModelSetting.user_id]", 
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)  # UUID
    original_filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="processing")  # processing/ready/failed
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationship
    owner = relationship("User", back_populates="documents")


class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    document_ids = Column(Text, nullable=True)  # JSON string
    chunks_retrieved = Column(Integer, nullable=True)
    provider = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    response_time = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # NEW: Track which model was actually used
    model_used = Column(String(100), nullable=True)
    model_cost_actual = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="queries")


# NEW: Import the model settings models so they're registered
from app.models.model_settings import ModelSetting, ModelPreset