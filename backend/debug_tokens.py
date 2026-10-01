"""
Script de diagnóstico para verificar uso de tokens
Ejecutar: python debug_tokens.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service
from app.services.llm_service import llm_service
from app.services.text_chunker import text_chunker
from app.models.database import User, Document
import tiktoken

# Inicializar tokenizer de OpenAI (aproximado para contar tokens)
tokenizer = tiktoken.get_encoding("cl100k_base")

def contar_tokens(texto: str) -> int:
    """Cuenta tokens aproximados en un texto"""
    return len(tokenizer.encode(texto))

def diagnosticar_configuracion():
    """Verifica la configuración actual"""
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN DEL SISTEMA")
    print("="*60)
    
    print(f"\n📋 Variables de entorno (.env):")
    print(f"├─ CHUNK_SIZE: {settings.CHUNK_SIZE}")
    print(f"├─ CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
    print(f"├─ TOP_K_RESULTS: {settings.TOP_K_RESULTS}")
    print(f"├─ DEFAULT_MODEL: {settings.DEFAULT_MODEL}")
    print(f"└─ SIMILARITY_THRESHOLD: {settings.SIMILARITY_THRESHOLD}")
    
    print(f"\n🔤 Tokenizer:")
    print(f"└─ Usando: tiktoken (cl100k_base) para estimación")

def diagnosticar_chunks(db, user_id: int, doc_id: str = None):
    """Verifica los chunks almacenados en ChromaDB"""
    print("\n" + "="*60)
    print("📦 ANÁLISIS DE CHUNKS EN VECTOR STORE")
    print("="*60)
    
    # Obtener estadísticas del vector store
    stats = vector_store_service.get_stats()
    print(f"\n📊 Estadísticas generales:")
    print(f"├─ Total chunks en DB: {stats.get('count', 0)}")
    print(f"└─ Dimensiones: {stats.get('dimensions', 0)}")
    
    # Buscar chunks de un usuario específico
    try:
        # Hacer una búsqueda dummy para ver qué chunks se recuperan
        query_embedding = embedding_service.encode_text("test query")
        
        results = vector_store_service.collection.query(
            query_embeddings=[query_embedding],
            where={"user_id": user_id},
            n_results=settings.TOP_K_RESULTS,
            include=["documents", "metadatas"]
        )
        
        chunks = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        if chunks:
            print(f"\n🔍 Chunks recuperados (TOP {settings.TOP_K_RESULTS}):")
            total_chars = 0
            total_tokens = 0
            
            for i, (chunk, meta) in enumerate(zip(chunks, metadatas), 1):
                chunk_chars = len(chunk)
                chunk_tokens = contar_tokens(chunk)
                total_chars += chunk_chars
                total_tokens += chunk_tokens
                
                print(f"\n  Chunk #{i}:")
                print(f"  ├─ Caracteres: {chunk_chars}")
                print(f"  ├─ Tokens estimados: {chunk_tokens}")
                print(f"  ├─ Document ID: {meta.get('document_id', 'N/A')}")
                print(f"  ├─ Chunk index: {meta.get('chunk_index', 'N/A')}")
                print(f"  └─ Preview: {chunk[:100]}...")
            
            print(f"\n📊 TOTALES:")
            print(f"├─ Total caracteres: {total_chars:,}")
            print(f"└─ Total tokens estimados: {total_tokens:,}")
            
        else:
            print("\n⚠️  No se encontraron chunks para este usuario")
            
    except Exception as e:
        print(f"\n❌ Error al analizar chunks: {e}")

def diagnosticar_prompt(question: str, chunks: list):
    """Analiza el prompt completo que se envía al LLM"""
    print("\n" + "="*60)
    print("💬 ANÁLISIS DEL PROMPT COMPLETO")
    print("="*60)
    
    # Construir el prompt como lo hace el sistema
    prompt = llm_service.build_rag_prompt(question, chunks)
    
    prompt_tokens = contar_tokens(prompt)
    
    print(f"\n📝 Componentes del prompt:")
    print(f"├─ Longitud total: {len(prompt):,} caracteres")
    print(f"├─ Tokens estimados: {prompt_tokens:,}")
    print(f"└─ Pregunta: '{question}'")
    
    print(f"\n🔤 Tokens estimados por sección:")
    
    # Sistema prompt (aproximado)
    system_part = prompt.split("Context from document:")[0] if "Context from document:" in prompt else ""
    if system_part:
        system_tokens = contar_tokens(system_part)
        print(f"├─ Sistema prompt: ~{system_tokens} tokens")
    
    # Context chunks
    context_part = prompt.split("Context from document:")[1].split("Question:")[0] if "Context from document:" in prompt else ""
    if context_part:
        context_tokens = contar_tokens(context_part)
        print(f"├─ Contexto (chunks): ~{context_tokens} tokens")
    
    # Question
    question_tokens = contar_tokens(question)
    print(f"└─ Pregunta: ~{question_tokens} tokens")
    
    print(f"\n📄 Preview del prompt (primeros 500 chars):")
    print("─" * 60)
    print(prompt[:500])
    print("..." if len(prompt) > 500 else "")
    print("─" * 60)
    
    return prompt_tokens

def diagnosticar_documento(db, doc_id: str):
    """Analiza un documento específico"""
    print("\n" + "="*60)
    print("📄 ANÁLISIS DE DOCUMENTO")
    print("="*60)
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        print(f"\n❌ Documento {doc_id} no encontrado")
        return
    
    print(f"\n📋 Información del documento:")
    print(f"├─ ID: {doc.id}")
    print(f"├─ Nombre: {doc.original_filename}")
    print(f"├─ Estado: {doc.status}")
    print(f"├─ Páginas: {doc.page_count}")
    print(f"├─ Chunks: {doc.chunk_count}")
    print(f"└─ Tamaño: {doc.file_size:,} bytes")
    
    # Verificar chunks en vector store
    try:
        results = vector_store_service.collection.get(
            where={"document_id": doc_id},
            include=["documents", "metadatas"]
        )
        
        chunks = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        if chunks:
            print(f"\n📊 Análisis de {len(chunks)} chunks:")
            
            chunk_sizes_chars = [len(chunk) for chunk in chunks]
            chunk_sizes_tokens = [contar_tokens(chunk) for chunk in chunks]
            
            print(f"\nCaracteres por chunk:")
            print(f"├─ Mínimo: {min(chunk_sizes_chars):,}")
            print(f"├─ Máximo: {max(chunk_sizes_chars):,}")
            print(f"├─ Promedio: {sum(chunk_sizes_chars)//len(chunk_sizes_chars):,}")
            print(f"└─ Total: {sum(chunk_sizes_chars):,}")
            
            print(f"\nTokens por chunk (estimado):")
            print(f"├─ Mínimo: {min(chunk_sizes_tokens):,}")
            print(f"├─ Máximo: {max(chunk_sizes_tokens):,}")
            print(f"├─ Promedio: {sum(chunk_sizes_tokens)//len(chunk_sizes_tokens):,}")
            print(f"└─ Total: {sum(chunk_sizes_tokens):,}")
            
            # Mostrar distribución
            print(f"\n📈 Distribución de tamaños (tokens):")
            ranges = [(0, 250), (250, 500), (500, 750), (750, 1000), (1000, float('inf'))]
            for low, high in ranges:
                count = sum(1 for size in chunk_sizes_tokens if low <= size < high)
                if count > 0:
                    bar = "█" * (count * 50 // len(chunks))
                    print(f"  {low:4d}-{high if high != float('inf') else '+':>4} tokens: {bar} ({count})")
                    
    except Exception as e:
        print(f"\n❌ Error al analizar chunks: {e}")

def simular_consulta(db, user_id: int, question: str, doc_id: str = None):
    """Simula una consulta completa y muestra el desglose de tokens"""
    print("\n" + "="*60)
    print("🧪 SIMULACIÓN DE CONSULTA COMPLETA")
    print("="*60)
    
    print(f"\n❓ Pregunta: '{question}'")
    print(f"👤 User ID: {user_id}")
    if doc_id:
        print(f"📄 Document ID: {doc_id}")
    
    try:
        # 1. Generar embedding de la pregunta
        print(f"\n1️⃣  Generando embedding de la pregunta...")
        query_embedding = embedding_service.encode_text(question)
        print(f"   ✅ Embedding generado: {len(query_embedding)} dimensiones")
        
        # 2. Buscar chunks relevantes
        print(f"\n2️⃣  Buscando chunks relevantes...")
        where_filter = {"user_id": user_id}
        if doc_id:
            where_filter["document_id"] = doc_id
        
        results = vector_store_service.collection.query(
            query_embeddings=[query_embedding],
            where=where_filter,
            n_results=settings.TOP_K_RESULTS,
            include=["documents", "metadatas", "distances"]
        )
        
        chunks = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        print(f"   ✅ Encontrados: {len(chunks)} chunks")
        
        if chunks:
            print(f"\n   📊 Relevancia de chunks:")
            for i, (chunk, dist) in enumerate(zip(chunks, distances), 1):
                similarity = 1 - dist  # Convertir distancia a similitud
                tokens = contar_tokens(chunk)
                print(f"   Chunk #{i}: {tokens} tokens, similitud: {similarity:.3f}")
        
        # 3. Construir prompt
        print(f"\n3️⃣  Construyendo prompt...")
        prompt_tokens = diagnosticar_prompt(question, chunks)
        
        # 4. Estimar tokens de respuesta
        print(f"\n4️⃣  Estimación de respuesta:")
        estimated_output = 350  # Estimación conservadora
        print(f"   📤 Tokens output estimados: ~{estimated_output}")
        
        # 5. Calcular costo
        print(f"\n5️⃣  Cálculo de costo:")
        model_pricing = {
            "anthropic/claude-sonnet-4": (3.0, 15.0),
            "anthropic/claude-3.5-haiku": (0.8, 4.0),
        }
        
        model = settings.DEFAULT_MODEL
        if model in model_pricing:
            input_price, output_price = model_pricing[model]
            
            input_cost = (prompt_tokens / 1_000_000) * input_price
            output_cost = (estimated_output / 1_000_000) * output_price
            total_cost = input_cost + output_cost
            
            print(f"\n   💰 Modelo: {model}")
            print(f"   ├─ Input: {prompt_tokens} tokens × ${input_price}/M = ${input_cost:.6f}")
            print(f"   ├─ Output: ~{estimated_output} tokens × ${output_price}/M = ${output_cost:.6f}")
            print(f"   └─ TOTAL: ${total_cost:.6f}")
            
            print(f"\n   📊 Costo mensual estimado (500 consultas/día):")
            daily = total_cost * 500
            monthly = daily * 30
            print(f"   ├─ Diario: ${daily:.2f}")
            print(f"   └─ Mensual: ${monthly:.2f}")
        
    except Exception as e:
        print(f"\n❌ Error en simulación: {e}")
        import traceback
        traceback.print_exc()

def menu_principal():
    """Menú interactivo"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🔍 DIAGNÓSTICO DE TOKENS - RAG SYSTEM")
        print("="*60)
        
        # Listar usuarios disponibles
        users = db.query(User).all()
        if not users:
            print("\n❌ No hay usuarios en el sistema")
            return
        
        print("\n👥 Usuarios disponibles:")
        for i, user in enumerate(users, 1):
            doc_count = db.query(Document).filter(
                Document.user_id == user.id,
                Document.status == "ready"
            ).count()
            print(f"{i}. {user.email} (ID: {user.id}) - {doc_count} documentos")
        
        user_choice = input("\nSelecciona usuario (número): ")
        try:
            user = users[int(user_choice) - 1]
        except:
            print("❌ Selección inválida")
            return
        
        while True:
            print("\n" + "="*60)
            print("📋 OPCIONES DE DIAGNÓSTICO")
            print("="*60)
            print("1. Ver configuración del sistema")
            print("2. Analizar chunks en vector store")
            print("3. Analizar documento específico")
            print("4. Simular consulta completa")
            print("5. Salir")
            
            choice = input("\nSelecciona opción: ")
            
            if choice == "1":
                diagnosticar_configuracion()
                
            elif choice == "2":
                diagnosticar_chunks(db, user.id)
                
            elif choice == "3":
                docs = db.query(Document).filter(
                    Document.user_id == user.id,
                    Document.status == "ready"
                ).all()
                
                if not docs:
                    print("\n❌ No hay documentos procesados")
                    continue
                
                print("\n📄 Documentos disponibles:")
                for i, doc in enumerate(docs, 1):
                    print(f"{i}. {doc.original_filename} ({doc.chunk_count} chunks)")
                
                doc_choice = input("\nSelecciona documento (número): ")
                try:
                    doc = docs[int(doc_choice) - 1]
                    diagnosticar_documento(db, doc.id)
                except:
                    print("❌ Selección inválida")
                    
            elif choice == "4":
                question = input("\n❓ Escribe tu pregunta: ")
                if not question:
                    question = "¿Cómo instalar fibra óptica?"
                
                use_doc = input("¿Buscar en documento específico? (s/n): ").lower() == 's'
                doc_id = None
                
                if use_doc:
                    docs = db.query(Document).filter(
                        Document.user_id == user.id,
                        Document.status == "ready"
                    ).all()
                    
                    if docs:
                        print("\n📄 Documentos:")
                        for i, doc in enumerate(docs, 1):
                            print(f"{i}. {doc.original_filename}")
                        
                        doc_choice = input("\nSelecciona documento (número): ")
                        try:
                            doc_id = docs[int(doc_choice) - 1].id
                        except:
                            pass
                
                simular_consulta(db, user.id, question, doc_id)
                
            elif choice == "5":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
            
            input("\n⏎ Presiona ENTER para continuar...")
            
    finally:
        db.close()

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()