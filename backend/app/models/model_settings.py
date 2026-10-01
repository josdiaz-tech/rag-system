# backend/backend/app/models/model_settings.py
"""
Database models for dynamic model management
These are NEW tables and don't affect existing functionality
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ModelSetting(Base):
    """
    Store model settings with scope hierarchy:
    - Global: Applies to all users (scope='global', user_id=NULL)
    - User: Applies to specific user (scope='user', user_id=X)
    """
    __tablename__ = "model_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(20), nullable=False)  # 'global' or 'user'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    model_id = Column(String(100), nullable=False)  # e.g., 'anthropic/claude-3.5-haiku'
    model_name = Column(String(100), nullable=True)  # Friendly name
    temperature = Column(Float, default=0.3)
    max_tokens = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="model_settings")
    creator = relationship("User", foreign_keys=[created_by])


class ModelPreset(Base):
    """
    Pre-configured model presets with cost/quality information
    Used to provide easy selection for admins
    """
    __tablename__ = "model_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    preset_name = Column(String(50), unique=True, nullable=False)  # 'premium', 'balanced', 'economy'
    model_id = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    estimated_cost_per_1k_tokens = Column(Float, nullable=False)
    quality_score = Column(Integer, nullable=False)  # 1-10
    speed_score = Column(Integer, nullable=False)  # 1-10
    is_active = Column(Boolean, default=True)