# RAG Document Q&A System - Setup Guide

## 🎯 Quick Start (Para tener todo funcionando HOY)

Este es un sistema RAG completo que permite subir PDFs y hacer preguntas sobre ellos usando IA.

### ✅ Pre-requisitos

Verifica que tengas instalado:
```bash
python3 --version  # Necesitas 3.10+
node --version     # Necesitas 18+ (para frontend más adelante)
git --version
```

### 🚀 Setup en 5 Pasos

#### Paso 1: Clonar/Copiar el Proyecto

```bash
# Si tienes el proyecto en un zip o carpeta, ve a ese directorio
cd ruta/al/proyecto
```

#### Paso 2: Configurar Backend

```bash
cd backend

# Crear ambiente virtual
python3 -m venv venv

# Activar ambiente virtual
# En Mac/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**⏱️ Esto tardará 5-10 minutos** (descarga modelos de embeddings)

#### Paso 3: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env (usa nano, vim, o tu editor favorito)
nano .env
```

**CRÍTICO: Edita estas variables:**
```bash
# Cambia esto a una clave secreta real
SECRET_KEY=tu-clave-super-secreta-aqui-minimo-32-caracteres

# Añade tu API key de OpenRouter
OPENROUTER_API_KEY=tu-api-key-de-openrouter

# Opcional: Usa SQLite para empezar rápido (ya configurado por defecto)
DATABASE_URL=sqlite:///./rag.db
```

**Para obtener OPENROUTER_API_KEY:**
1. Ve a https://openrouter.ai
2. Regístrate/Inicia sesión
3. Ve a https://openrouter.ai/keys
4. Crea una nueva API key
5. Añade créditos con Zinli

#### Paso 4: Iniciar el Backend

```bash
# Asegúrate de estar en /backend con el venv activado
python main.py
```

**Verás algo como:**
```
==================================================
🚀 Starting RAG Document Q&A System
==================================================
✅ Database tables created successfully!
🔄 Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
📍 Using device: cpu
✅ Embedding model loaded successfully!
🔄 Initializing ChromaDB at: ../chroma_db
✅ ChromaDB initialized! Collection has 0 chunks
✅ LLM Service initialized with model: anthropic/claude-sonnet-4
✅ RAG Pipeline initialized
==================================================
✅ System ready!
📚 API Documentation: http://localhost:8000/docs
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Paso 5: ¡Probar el Sistema!

Abre tu navegador y ve a: **http://localhost:8000/docs**

Verás la interfaz Swagger con todos los endpoints disponibles.

---

## 🧪 Probando el Sistema (Sin Frontend)

### 1. Registrar un Usuario

En Swagger UI:
1. Ve a `POST /api/auth/register`
2. Click en "Try it out"
3. Usa este JSON:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!",
  "full_name": "Test User"
}
```
4. Click "Execute"

### 2. Hacer Login

1. Ve a `POST /api/auth/login`
2. Usa:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!"
}
```
3. **COPIA el `access_token`** de la respuesta

### 3. Autenticarte en Swagger

1. Click en el botón "Authorize" (arriba a la derecha)
2. Pega el token (con "Bearer " adelante):
   ```
   Bearer tu-token-aqui
   ```
3. Click "Authorize"

### 4. Subir un PDF

1. Ve a `POST /api/documents/upload`
2. Click "Try it out"
3. Click "Choose File" y selecciona un PDF
4. Click "Execute"
5. **Copia el `id` del documento** de la respuesta

### 5. Verificar Procesamiento

1. Ve a `GET /api/documents/{document_id}/status`
2. Usa el `id` del paso anterior
3. Espera hasta que `status` sea `"ready"` (puede tardar 30-60 segundos)

### 6. ¡Hacer Preguntas!

1. Ve a `POST /api/query/`
2. Usa:
```json
{
  "question": "¿De qué trata este documento?"
}
```
3. ¡Recibirás una respuesta basada en tu PDF!

---

## 📁 Estructura del Proyecto

```
backend/
├── main.py                          # Aplicación FastAPI principal
├── requirements.txt                 # Dependencias Python
├── .env                            # Variables de entorno (NO subir a Git)
├── .env.example                    # Plantilla de variables
│
├── app/
│   ├── core/
│   │   ├── config.py               # Configuración
│   │   ├── database.py             # Conexión a DB
│   │   └── security.py             # JWT y autenticación
│   │
│   ├── models/
│   │   ├── database.py             # Modelos SQLAlchemy
│   │   └── schemas.py              # Schemas Pydantic
│   │
│   ├── api/
│   │   ├── auth.py                 # Endpoints de autenticación
│   │   ├── documents.py            # Endpoints de documentos
│   │   └── query.py                # Endpoints de consultas
│   │
│   └── services/
│       ├── document_processor.py   # Procesamiento de PDFs
│       ├── text_chunker.py         # Chunking de texto
│       ├── embedding_service.py    # Embeddings locales
│       ├── vector_store.py         # ChromaDB
│       ├── llm_service.py          # OpenRouter/Claude
│       └── rag_pipeline.py         # Pipeline completo
│
├── uploads/                        # PDFs subidos
├── chroma_db/                      # Base de datos vectorial
└── rag.db                          # Base de datos SQLite
```

---

## 🔧 Características Implementadas

### ✅ Autenticación Segura
- Registro de usuarios
- Login con JWT
- Passwords hasheados con bcrypt
- Tokens con expiración

### ✅ Procesamiento de Documentos
- Upload de PDFs
- Extracción de texto con PyMuPDF
- Sanitización contra prompt injection
- Chunking inteligente con overlap
- Embeddings locales (GRATIS)
- Almacenamiento vectorial con ChromaDB

### ✅ Sistema de Consultas
- Búsqueda semántica en documentos
- Respuestas generadas con Claude Sonnet 4
- Citación de fuentes
- Historial de consultas

### ✅ Multi-Usuario
- Aislamiento de datos por usuario
- Cada usuario solo ve sus documentos
- Filtrado seguro en vector store

### ✅ Seguridad
- Validación de archivos
- Prevención de path traversal
- Sanitización de texto
- Límites de tamaño
- Nombres de archivo seguros

---

## 🛠️ Troubleshooting

### Problema: "Module not found"
```bash
# Asegúrate de que el virtual environment esté activado
source venv/bin/activate  # Mac/Linux
# O
venv\Scripts\activate     # Windows

# Reinstala dependencias
pip install -r requirements.txt
```

### Problema: "OPENROUTER_API_KEY not set"
```bash
# Edita el archivo .env
nano .env

# Añade tu API key
OPENROUTER_API_KEY=sk-or-v1-tu-key-aqui
```

### Problema: Embeddings muy lentos
Esto es normal la primera vez que se carga el modelo (descarga ~90MB).
En Mac sin GPU puede tardar 2-3 segundos por chunk. Considera:
- Usar chunks más pequeños
- Procesar documentos más cortos
- Más adelante: añadir GPU

### Problema: "Database locked" (SQLite)
SQLite no maneja bien la concurrencia. Para producción:
```bash
# En .env, cambia a PostgreSQL:
DATABASE_URL=postgresql://user:pass@localhost:5432/rag_db
```

---

## 📊 Costos Estimados

### GRATIS
- Embeddings (sentence-transformers local)
- Vector DB (ChromaDB local)
- Base de datos (SQLite local)

### De Pago
- **OpenRouter API**: ~$3-15 por millón de tokens
  - Query simple: ~$0.01
  - Query compleja: ~$0.05
  - 100 queries/día ≈ $30-50/mes

---

## 🚀 Próximos Pasos

### Ahora que tienes el backend funcionando:

1. **Prueba con PDFs reales** - Sube varios documentos
2. **Experimenta con preguntas** - Prueba diferentes tipos de consultas
3. **Frontend** - Crea una interfaz web (React/Vue/Svelte)
4. **Deploy** - Despliega en un servidor real
5. **Optimización** - Ajusta parámetros del RAG

### Para Mejorar:
- [ ] Añadir caché de queries (Redis)
- [ ] OCR para PDFs escaneados (Tesseract)
- [ ] Soporte para más formatos (DOCX, TXT)
- [ ] Rate limiting
- [ ] Analytics dashboard
- [ ] Migrar a PostgreSQL
- [ ] Añadir tests

---

## 📞 Soporte

**Documentación Oficial:**
- FastAPI: https://fastapi.tiangolo.com
- LangChain: https://python.langchain.com
- ChromaDB: https://docs.trychroma.com
- OpenRouter: https://openrouter.ai/docs

**Tu Checklist y Especificación Técnica:**
- Ver `CHECKLIST.md` para próximos pasos
- Ver `rag-mvp-technical-spec.md` para arquitectura completa

---

## ⚠️ Advertencias Importantes

1. **NO subas `.env` a Git** - Contiene secrets
2. **El SECRET_KEY debe ser único y secreto**
3. **SQLite solo para desarrollo** - Usa PostgreSQL en producción
4. **Embeddings tardan** - Primera carga del modelo toma tiempo
5. **OpenRouter cuesta dinero** - Monitorea tu uso

---

## ✅ Checklist de Verificación

Antes de decir que está funcionando, verifica:

- [ ] Backend inicia sin errores
- [ ] Puedes registrar un usuario
- [ ] Puedes hacer login y obtener token
- [ ] Puedes subir un PDF
- [ ] El documento se procesa (status = "ready")
- [ ] Puedes hacer una pregunta
- [ ] Recibes una respuesta coherente
- [ ] La respuesta incluye fuentes del documento

Si todos los checks están ✅, **¡TIENES UN RAG FUNCIONANDO!** 🎉

---

**Versión:** 1.0.0  
**Fecha:** 2025-11-10  
**Stack:** FastAPI + ChromaDB + Claude Sonnet 4
