# backend/backend/create_model_tables.py
"""
Database migration script to add model management tables
Run this ONCE to create the new tables
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_model_tables():
    """Create model_settings and model_presets tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create model_settings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope VARCHAR(20) NOT NULL,
                user_id INTEGER,
                model_id VARCHAR(100) NOT NULL,
                model_name VARCHAR(100),
                temperature FLOAT DEFAULT 0.3,
                max_tokens INTEGER DEFAULT 1000,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """))
        
        # Create model_presets table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_name VARCHAR(50) NOT NULL UNIQUE,
                model_id VARCHAR(100) NOT NULL,
                description TEXT,
                estimated_cost_per_1k_tokens FLOAT NOT NULL,
                quality_score INTEGER NOT NULL,
                speed_score INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        
        # Add new columns to queries table (if they don't exist)
        try:
            conn.execute(text("ALTER TABLE queries ADD COLUMN model_used VARCHAR(100)"))
        except:
            pass  # Column already exists
        
        try:
            conn.execute(text("ALTER TABLE queries ADD COLUMN model_cost_actual FLOAT"))
        except:
            pass  # Column already exists
        
        conn.commit()
        print("✅ Model management tables created successfully!")

if __name__ == "__main__":
    create_model_tables()