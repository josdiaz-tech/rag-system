# backend/backend/app/api/admin.py
"""
Admin API endpoints for model management
All endpoints require admin privileges
These are BRAND NEW - don't affect existing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.models.database import User
from app.models.model_settings import ModelSetting, ModelPreset
from app.services.model_manager import model_manager
from pydantic import BaseModel, Field
from datetime import datetime


router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== SCHEMAS (Defined here to keep admin isolated) ====================

class ModelSettingCreate(BaseModel):
    """Create new model setting"""
    scope: str = Field(..., pattern="^(global|user)$", description="'global' or 'user'")
    user_id: Optional[int] = Field(None, description="Required if scope='user'")
    model_id: str = Field(..., description="OpenRouter model ID")
    model_name: Optional[str] = Field(None, description="Friendly name")
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=100, le=4000)


class ModelSettingResponse(BaseModel):
    """Model setting response"""
    id: int
    scope: str
    user_id: Optional[int]
    model_id: str
    model_name: Optional[str]
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModelPresetResponse(BaseModel):
    """Model preset response"""
    id: int
    preset_name: str
    model_id: str
    description: Optional[str]
    estimated_cost_per_1k_tokens: float
    quality_score: int
    speed_score: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ModelConfigResponse(BaseModel):
    """Current model configuration"""
    model_id: str
    temperature: float
    max_tokens: int
    source: str  # 'default', 'global', 'user', 'query_override'


# ==================== HELPER FUNCTIONS ====================

def verify_admin(current_user: User = Depends(get_current_active_user)):
    """Verify user has admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# ==================== MODEL SETTINGS ENDPOINTS ====================

@router.get("/models/settings", response_model=List[ModelSettingResponse])
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def list_model_settings(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    **[ADMIN ONLY]** List all active model settings
    
    Shows both global and user-specific settings
    """
    settings_list = db.query(ModelSetting).filter(
        ModelSetting.is_active == True
    ).order_by(ModelSetting.created_at.desc()).all()
    
    return settings_list


@router.get("/models/settings/global", response_model=ModelSettingResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_global_model_setting(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    **[ADMIN ONLY]** Get current global model setting
    
    Returns the model configuration applied to all users
    """
    setting = db.query(ModelSetting).filter(
        ModelSetting.scope == "global",
        ModelSetting.is_active == True
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No global model setting found (using default from .env)"
        )
    
    return setting


@router.post("/models/settings/global", response_model=ModelSettingResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def set_global_model(
    request: Request,
    response: Response,
    setting: ModelSettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    **[ADMIN ONLY]** Set global model for entire system
    
    This will apply to ALL users who don't have user-specific settings
    
    **Example:**
```json
    {
      "scope": "global",
      "model_id": "anthropic/claude-3.5-haiku",
      "model_name": "Claude 3.5 Haiku (Balanced)",
      "temperature": 0.3,
      "max_tokens": 1000
    }
```
    """
    # Validate model
    if not model_manager.validate_model_id(setting.model_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model ID: {setting.model_id}. Check /admin/models/presets for available models."
        )
    
    # Must be global scope
    if setting.scope != "global":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for global settings only. Use /user/{user_id} for user-specific."
        )
    
    # Deactivate existing global setting
    db.query(ModelSetting).filter(
        ModelSetting.scope == "global",
        ModelSetting.is_active == True
    ).update({"is_active": False})
    
    # Create new global setting
    new_setting = ModelSetting(
        scope="global",
        user_id=None,
        model_id=setting.model_id,
        model_name=setting.model_name,
        temperature=setting.temperature,
        max_tokens=setting.max_tokens,
        created_by=current_user.id
    )
    
    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)
    
    return new_setting


@router.post("/models/settings/user/{user_id}", response_model=ModelSettingResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def set_user_model(
    request: Request,
    response: Response,
    user_id: int,
    setting: ModelSettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    **[ADMIN ONLY]** Set model for specific user
    
    Override global setting for a specific client
    Useful for giving VIP clients premium models
    
    **Example:**
```json
    {
      "scope": "user",
      "user_id": 5,
      "model_id": "anthropic/claude-sonnet-4",
      "model_name": "Claude Sonnet 4 (Premium)",
      "temperature": 0.2,
      "max_tokens": 2000
    }
```
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Validate model
    if not model_manager.validate_model_id(setting.model_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model ID: {setting.model_id}"
        )
    
    # Deactivate existing user setting
    db.query(ModelSetting).filter(
        ModelSetting.scope == "user",
        ModelSetting.user_id == user_id,
        ModelSetting.is_active == True
    ).update({"is_active": False})
    
    # Create new user setting
    new_setting = ModelSetting(
        scope="user",
        user_id=user_id,
        model_id=setting.model_id,
        model_name=setting.model_name,
        temperature=setting.temperature,
        max_tokens=setting.max_tokens,
        created_by=current_user.id
    )
    
    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)
    
    return new_setting


@router.delete("/models/settings/{setting_id}")
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def delete_model_setting(
    request: Request,
    response: Response,
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    **[ADMIN ONLY]** Delete (deactivate) a model setting
    
    System will fall back to next level in hierarchy
    """
    setting = db.query(ModelSetting).filter(ModelSetting.id == setting_id).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    setting.is_active = False
    db.commit()
    
    return {"message": "Model setting deactivated", "id": setting_id}


# ==================== MODEL PRESETS ENDPOINTS ====================

@router.get("/models/presets", response_model=List[ModelPresetResponse])
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def list_model_presets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # Any user can see presets
):
    """
    List available model presets with cost/quality information
    
    **Available to all users** (not just admins)
    
    Use these preset names when setting models:
    - `premium`: Best quality, highest cost
    - `balanced`: Good quality, moderate cost (RECOMMENDED)
    - `economy`: Decent quality, low cost
    - `ultra_economy`: Basic quality, lowest cost
    """
    presets = db.query(ModelPreset).filter(ModelPreset.is_active == True).all()
    return presets


# ==================== MODEL INFO ENDPOINTS ====================

@router.get("/models/current", response_model=ModelConfigResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_current_model_config(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the model configuration that will be used for this user
    
    **Available to all users**
    
    Shows which model, temperature, and max_tokens will be used
    Also shows the source (default/global/user/query_override)
    """
    config = model_manager.get_model_config(db, current_user.id)
    return config


@router.get("/models/supported")
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_supported_models(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all supported model IDs
    
    **Available to all users**
    """
    return {
        "supported_models": model_manager.supported_models,
        "default_model": model_manager.default_model
    }