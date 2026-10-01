# RAG System - Guía Rápida de Inicio

## 🎯 Meta: Tener el sistema respondiendo preguntas de PDFs en 30 minutos

### Paso 1: Setup Inicial (10 min)

```bash
# 1. Ve a la carpeta del proyecto
cd ruta/al/proyecto/backend

# 2. Crea ambiente virtual
python3 -m venv venv

# 3. Activa ambiente virtual
source venv/bin/activate

# 4. Instala dependencias
pip install -r requirements.txt
```

⏱️ **Esto tardará 5-10 min** (descarga modelo de embeddings)

---

### Paso 2: Configurar API Key (5 min)

```bash
# 1. Copia el archivo de configuración
cp .env.example .env

# 2. Edita .env
nano .env
```

**Cambia estas 2 líneas:**
```
SECRET_KEY=cambia-esto-por-algo-super-secreto-minimo-32-caracteres
OPENROUTER_API_KEY=tu-api-key-aqui
```

**Para obtener API key:**
1. https://openrouter.ai → Regístrate
2. https://openrouter.ai/keys → Crear key
3. Añade créditos con Zinli

---

### Paso 3: Iniciar Sistema (1 min)

```bash
# Asegúrate de estar en /backend con venv activado
python main.py
```

**Deberías ver:**
```
✅ System ready!
📚 API Documentation: http://localhost:8000/docs
```

---

### Paso 4: Probar (10 min)

Abre navegador: **http://localhost:8000/docs**

#### A. Registrar Usuario
1. `POST /api/auth/register` → Try it out
2. JSON:
```json
{
  "email": "test@test.com",
  "password": "SecurePass123!",
  "full_name": "Test"
}
```

#### B. Login
1. `POST /api/auth/login`
2. JSON:
```json
{
  "email": "test@test.com",
  "password": "SecurePass123!"
}
```
3. **COPIA el access_token**

#### C. Autenticar
1. Click botón "Authorize" (arriba)
2. Pega: `Bearer tu-token-aqui`
3. Authorize

#### D. Subir PDF
1. `POST /api/documents/upload`
2. Choose File → selecciona un PDF
3. Execute
4. **COPIA el id del documento**

#### E. Esperar Procesamiento
1. `GET /api/documents/{document_id}/status`
2. Usa el id copiado
3. Espera hasta que status = "ready" (30-60 seg)

#### F. ¡Hacer Pregunta!
1. `POST /api/query/`
2. JSON:
```json
{
  "question": "¿De qué trata este documento?"
}
```
3. **¡Recibirás respuesta basada en tu PDF!** 🎉

---

## ✅ Checklist de Verificación

- [ ] Backend inicia sin errores
- [ ] Puedo registrarme
- [ ] Puedo hacer login
- [ ] Puedo subir PDF
- [ ] PDF se procesa (status="ready")
- [ ] Puedo hacer pregunta
- [ ] Recibo respuesta coherente

**Si todo funciona: ¡TIENES UN RAG ANDANDO!** 🚀

---

## 🛠️ Troubleshooting Rápido

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "OPENROUTER_API_KEY not set"
```bash
nano .env
# Añade tu key
```

### "Connection refused"
```bash
# ¿El backend está corriendo?
python main.py
```

---

## 📊 Estructura de Archivos Creados

```
backend/
├── main.py                 # App principal
├── requirements.txt        # Dependencias
├── .env                    # Config (NO subir a Git)
├── test_system.py          # Script de pruebas
│
├── app/
│   ├── core/
│   │   ├── config.py       # Configuración
│   │   ├── database.py     # Base de datos
│   │   └── security.py     # Autenticación
│   │
│   ├── models/
│   │   ├── database.py     # Modelos DB
│   │   └── schemas.py      # Validación
│   │
│   ├── api/
│   │   ├── auth.py         # Login/Register
│   │   ├── documents.py    # Subir PDFs
│   │   └── query.py        # Hacer preguntas
│   │
│   └── services/
│       ├── document_processor.py   # Procesar PDFs
│       ├── text_chunker.py         # Dividir texto
│       ├── embedding_service.py    # Embeddings (GRATIS)
│       ├── vector_store.py         # ChromaDB
│       ├── llm_service.py          # Claude/OpenRouter
│       └── rag_pipeline.py         # Pipeline completo
│
├── uploads/         # PDFs subidos
├── chroma_db/       # Base vectorial
└── rag.db          # SQLite
```

---

## 💰 Costos

**GRATIS:**
- Embeddings (local)
- Vector DB (local)
- Base de datos (local)

**De Pago:**
- OpenRouter: ~$0.01 por query simple
- ~$30-50/mes para 100 queries/día

---

## 🚀 Próximos Pasos

1. ✅ Tienes backend funcionando
2. ⬜ Prueba con varios PDFs
3. ⬜ Crea frontend (React/Vue/Svelte)
4. ⬜ Deploy a servidor
5. ⬜ Añade features extra

**Ver README.md completo para más detalles**

---

**Versión:** 1.0  
**Fecha:** 2025-11-10  
**Stack:** FastAPI + ChromaDB + Claude Sonnet 4
