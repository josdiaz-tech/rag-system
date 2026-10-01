# backend/backend/app/api/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    validate_password_strength
)
from app.core.config import settings
from app.core.logging_config import get_logger, get_security_logger
from app.core.rate_limiter import limiter
from app.models.database import User
from app.models.schemas import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)
security_logger = get_security_logger()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    response: Response,  # ADDED: Required by slowapi
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    **Rate limit:** Configurable via RATE_LIMIT_AUTH (default: 10/hour)
    
    Password requirements:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        security_logger.warning("Registration failed - email already exists", extra={
            "email": user_data.email,
            "event": "registration_failed",
            "reason": "email_exists"
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    if not validate_password_strength(user_data.password):
        security_logger.warning("Registration failed - weak password", extra={
            "email": user_data.email,
            "event": "registration_failed",
            "reason": "weak_password"
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements. Must be 12+ characters with uppercase, lowercase, digit, and special character."
        )
    
    # Check if email is in admin list
    is_admin = user_data.email.lower() in settings.get_admin_emails()
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_admin=is_admin  # Auto-assign admin if in list
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    if is_admin:
        print(f"✅ Admin user registered: {user_data.email}")

    
    logger.info("User registered successfully", extra={
        "user_id": new_user.id,
        "email": new_user.email,
        "event": "user_registered"
    })
    
    return new_user


@router.post("/token", response_model=Token)
@limiter.limit(lambda: settings.RATE_LIMIT_AUTH)
async def login_for_swagger(
    request: Request,
    response: Response,  # ADDED: Required by slowapi
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint for Swagger UI
    
    **Rate limit:** Configurable via RATE_LIMIT_AUTH (default: 10/hour)
    
    - Use **email** as username
    - Password is your account password
    
    This endpoint is specifically for Swagger UI's "Authorize" button.
    For programmatic access, use /login endpoint instead.
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we use email
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        security_logger.warning("Login failed - invalid credentials", extra={
            "email": form_data.username,
            "event": "login_failed",
            "endpoint": "/token"
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    logger.info("User logged in successfully", extra={
        "user_id": user.id,
        "email": user.email,
        "event": "user_login",
        "endpoint": "/token"
    })
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
@limiter.limit(lambda: settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    response: Response,  # ADDED: Required by slowapi
    user_credentials: UserLogin, 
    db: Session = Depends(get_db)
):
    """
    Login and get JWT access token (JSON body)
    
    **Rate limit:** Configurable via RATE_LIMIT_AUTH (default: 10/hour)
    
    This endpoint accepts JSON with email and password.
    For Swagger UI, use /token endpoint instead.
    """
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        security_logger.warning("Login failed - invalid credentials", extra={
            "email": user_credentials.email,
            "event": "login_failed",
            "endpoint": "/login"
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    logger.info("User logged in successfully", extra={
        "user_id": user.id,
        "email": user.email,
        "event": "user_login",
        "endpoint": "/login"
    })
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
@limiter.limit(lambda: settings.RATE_LIMIT_GENERAL)
async def get_current_user_info(
    request: Request,
    response: Response,  # ADDED: Required by slowapi
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    **Rate limit:** Configurable via RATE_LIMIT_GENERAL (default: 100/hour)
    """
    return current_user