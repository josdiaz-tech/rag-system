# backend/backend/test_hyde.py
"""
Test HyDE functionality without breaking existing system
"""

import asyncio
import sys
sys.path.append('.')

from app.core.config import settings
from app.services.hyde_retriever import hyde_retriever
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service


async def test_hyde():
    """Test HyDE hypothesis generation"""
    
    print("="*80)
    print("🧪 TESTING HYDE (Hypothetical Document Embeddings)")
    print("="*80)
    
    # Check if HyDE is enabled
    print(f"\n📋 Configuration:")
    print(f"   ENABLE_HYDE: {settings.ENABLE_HYDE}")
    print(f"   HYDE_MODEL: {settings.HYDE_MODEL}")
    print(f"   HYDE_FALLBACK_MODE: {settings.HYDE_FALLBACK_MODE}")
    print(f"   HYDE_MIN_RESULTS_THRESHOLD: {settings.HYDE_MIN_RESULTS_THRESHOLD}")
    
    if not settings.ENABLE_HYDE:
        print(f"\n⚠️  HyDE is DISABLED in config.py")
        print(f"   To enable: Set ENABLE_HYDE = True in .env file")
        return
    
    if not hyde_retriever.is_available():
        print(f"\n❌ HyDE not available - check OPENROUTER_API_KEY")
        return
    
    # Test questions (semantic gap scenarios)
    test_questions = [
        "¿Cuál es la API del sistema?",
        "Dame la URL de la interfaz",
        "¿Dónde está el endpoint de consulta?",
        "¿Cómo accedo al servicio web?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"📝 Question: {question}")
        print(f"{'='*80}")
        
        # Generate hypothetical document
        print(f"\n🔮 Generating hypothetical document...")
        hyp_doc = await hyde_retriever.generate_hypothetical_document(question)
        
        print(f"\n📄 Hypothetical Document ({len(hyp_doc)} chars):")
        print(f"   {hyp_doc[:300]}...")
        
        # You can test retrieval here if you have documents uploaded
        # For now, just show the hypothesis generation works
    
    print(f"\n{'='*80}")
    print(f"✅ HyDE test completed!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_hyde())