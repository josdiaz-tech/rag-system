# backend/backend/app/utils/init_presets.py
"""
Initialize default model presets on system startup
Only runs once - won't duplicate existing presets
"""
from sqlalchemy.orm import Session
from app.models.model_settings import ModelPreset


def initialize_default_presets(db: Session):
    """
    Initialize default model presets if they don't exist
    Provides easy selection for admins
    """
    
    default_presets = [
        {
            "preset_name": "premium",
            "model_id": "anthropic/claude-sonnet-4",
            "description": "Razonamiento y precisión de la más alta calidad. Ideal para consultas técnicas complejas. La más cara.",
            "estimated_cost_per_1k_tokens": 0.009,
            "quality_score": 10,
            "speed_score": 6
        },
        {
            "preset_name": "balanced",
            "model_id": "anthropic/claude-3.5-haiku",
            "description": "Gran equilibrio entre calidad y costo. Recomendado para la mayoría de consultas. 5-6× más barato que el premium.",
            "estimated_cost_per_1k_tokens": 0.0024,
            "quality_score": 8,
            "speed_score": 8
        },
        {
            "preset_name": "economy",
            "model_id": "openai/gpt-4o-mini",
            "description": "Rentable para consultas factuales simples. 20× más barato que el premium. Buena calidad.",
            "estimated_cost_per_1k_tokens": 0.00045,
            "quality_score": 7,
            "speed_score": 9
        },
        {
            "preset_name": "ultra_economy",
            "model_id": "google/gemini-flash-1.5",
            "description": "Opción de menor costo. Ideal para consultas simples de alto volumen. 40× más barato que el premium.",
            "estimated_cost_per_1k_tokens": 0.0002,
            "quality_score": 6,
            "speed_score": 10
        }
    ]
    
    created_count = 0
    for preset_data in default_presets:
        existing = db.query(ModelPreset).filter(
            ModelPreset.preset_name == preset_data["preset_name"]
        ).first()
        
        if not existing:
            preset = ModelPreset(**preset_data)
            db.add(preset)
            created_count += 1
    
    if created_count > 0:
        db.commit()
        print(f"✅ Initialized {created_count} default model presets")
    else:
        print("ℹ️  Model presets already exist, skipping initialization")