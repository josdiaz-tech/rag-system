# backend/backend/app/services/model_manager.py
"""
Model Manager Service
Handles dynamic model selection with hierarchy:
1. Query-specific override (if provided)
2. User-specific setting (if exists)
3. Global override (if exists)
4. Default from .env
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.model_settings import ModelSetting, ModelPreset
from app.core.config import settings


class ModelManager:
    """
    Manages dynamic model selection
    100% backward compatible - existing code works without changes
    """
    
    def __init__(self):
        self.default_model = settings.DEFAULT_MODEL
        self.default_temperature = 0.3
        #son caracteres no tokens
        self.default_max_tokens = 3000
        
        # Supported models (can be expanded)
        self.supported_models = [
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.5-haiku",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5",
            "google/gemini-pro-1.5",
            "groq/llama-3.1-70b-versatile",
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-flash",
            "meta-llama/llama-3.3-70b-instruct"
        ]
    
    def get_model_config(
        self,
        db: Session,
        user_id: int,
        override_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the appropriate model configuration based on hierarchy
        
        Returns:
            {
                "model_id": str,
                "temperature": float,
                "max_tokens": int,
                "source": str  # 'query_override', 'user', 'global', 'default'
            }
        """
        
        # Level 4: Query-specific override (highest priority)
        if override_model:
            if self.validate_model_id(override_model):
                return {
                    "model_id": override_model,
                    "temperature": self.default_temperature,
                    "max_tokens": self.default_max_tokens,
                    "source": "query_override"
                }
        
        # Level 3: User-specific setting
        user_setting = db.query(ModelSetting).filter(
            ModelSetting.scope == "user",
            ModelSetting.user_id == user_id,
            ModelSetting.is_active == True
        ).first()
        
        if user_setting:
            return {
                "model_id": user_setting.model_id,
                "temperature": user_setting.temperature,
                "max_tokens": user_setting.max_tokens,
                "source": "user"
            }
        
        # Level 2: Global override
        global_setting = db.query(ModelSetting).filter(
            ModelSetting.scope == "global",
            ModelSetting.user_id == None,
            ModelSetting.is_active == True
        ).first()
        
        if global_setting:
            return {
                "model_id": global_setting.model_id,
                "temperature": global_setting.temperature,
                "max_tokens": global_setting.max_tokens,
                "source": "global"
            }
        
        # Level 1: Default from .env
        return {
            "model_id": self.default_model,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "source": "default"
        }
    
    def get_available_models(self, db: Session) -> list[Dict[str, Any]]:
        """Get list of available model presets"""
        presets = db.query(ModelPreset).filter(ModelPreset.is_active == True).all()
        
        return [
            {
                "preset_name": p.preset_name,
                "model_id": p.model_id,
                "description": p.description,
                "estimated_cost": p.estimated_cost_per_1k_tokens,
                "quality_score": p.quality_score,
                "speed_score": p.speed_score
            }
            for p in presets
        ]
    
    def validate_model_id(self, model_id: str) -> bool:
        """Validate if model_id is supported"""
        return model_id in self.supported_models


# Singleton instance
model_manager = ModelManager()