from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.database import User
from app.core.config import settings

def promote_to_admin(email: str):
    """Promote existing user to admin"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        if user.is_admin:
            print(f"ℹ️  User already admin: {email}")
            return
        
        user.is_admin = True
        db.commit()
        print(f"✅ Promoted to admin: {email}")
    finally:
        db.close()

def promote_all_admin_emails():
    """Promote all users in ADMIN_EMAILS env var"""
    admin_emails = settings.get_admin_emails()
    
    if not admin_emails:
        print("⚠️  No ADMIN_EMAILS configured in .env")
        return
    
    print(f"📧 Processing {len(admin_emails)} admin emails...")
    for email in admin_emails:
        promote_to_admin(email)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Promote specific email
        promote_to_admin(sys.argv[1])
    else:
        # Promote all from .env
        promote_all_admin_emails()