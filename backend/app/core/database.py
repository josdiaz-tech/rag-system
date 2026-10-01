from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.models import database
    from app.models import model_settings
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def drop_db():
    """Drop all database tables (use with caution!)"""
    from app.models import database
    from app.models import model_settings
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")