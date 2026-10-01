import os
import requests
import json

# Configuración
TOKEN = os.getenv("RAG_TOKEN", "your_jwt_token_here")
BASE_URL = "http://localhost:8000/api"

def query(question):
    """Hacer una pregunta al sistema RAG"""
    response = requests.post(
        f"{BASE_URL}/query/",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"question": question}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*60)
        print("PREGUNTA:", question)
        print("="*60)
        print("\nRESPUESTA:")
        print(result["answer"])
        print("\n" + "-"*60)
        print(f"Chunks: {result['chunks_retrieved']} | Tiempo: {result['response_time']:.2f}s")
        print("="*60 + "\n")
        
        # Mostrar fuentes si las hay
        if result.get("sources"):
            print("\nFUENTES:")
            for i, source in enumerate(result["sources"][:3], 1):
                print(f"{i}. {source['source_file']} (página aprox.)")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def list_documents():
    """Listar documentos"""
    response = requests.get(
        f"{BASE_URL}/documents/",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    if response.status_code == 200:
        docs = response.json()
        print("\n📚 TUS DOCUMENTOS:")
        print("="*60)
        for doc in docs:
            status_emoji = "✅" if doc["status"] == "ready" else "⏳"
            print(f"{status_emoji} {doc['original_filename']}")
            print(f"   ID: {doc['id']}")
            print(f"   Status: {doc['status']} | Chunks: {doc.get('chunk_count', 0)}")
            print()
        return docs
    else:
        print(f"Error: {response.status_code}")
        return None

# Uso
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python query.py 'tu pregunta aqui'")
        print("  python query.py --list  (listar documentos)")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_documents()
    else:
        question = " ".join(sys.argv[1:])
        query(question)
