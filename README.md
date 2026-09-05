# 🧠 Asistente IA - Psicología Clínica

Sistema de asistencia con inteligencia artificial para consultorios de psicología clínica.

## ¿Qué hace?

1. **Transcribe sesiones en tiempo real** — Captura el audio de la sesión (virtual o presencial) y lo convierte a texto con identificación de hablantes
2. **Analiza con IA** — Un LLM extrae datos clínicos relevantes de la transcripción (nombre, síntomas, diagnóstico, plan terapéutico, etc.)
3. **Genera documentos** — Rellena automáticamente la plantilla de historia clínica con los datos extraídos

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python + FastAPI |
| STT (Voz a Texto) | Deepgram Nova-3 (Streaming) |
| LLM (Análisis) | Google Gemini 2.5 Flash |
| Documentos | docxtpl (Jinja2 + Word) |
| Base de datos | SQLite (async) |
| Frontend | HTML + JavaScript |

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual (Windows)
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API keys en el archivo .env
# Editar .env con tus claves de Deepgram y Google AI Studio

# 5. Ejecutar el servidor
uvicorn app.main:app --reload
```

## Estructura del Proyecto

```
Asistente_psicologia/
├── app/                          # Backend (FastAPI)
│   ├── main.py                   # Aplicación principal + WebSocket
│   ├── config.py                 # Configuración y API keys
│   ├── database.py               # SQLite async
│   ├── models/
│   │   ├── schemas.py            # Pydantic schemas (datos clínicos)
│   │   └── db_models.py          # Modelos de base de datos
│   └── services/
│       ├── deepgram_service.py   # Streaming STT
│       ├── gemini_service.py     # LLM extracción de datos
│       └── document_service.py   # Generación de documentos
├── static/                       # Frontend
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── audio.js              # Captura de audio
│       └── app.js                # Lógica UI
├── templates/                    # Plantillas Word
│   └── historia_clinica.docx
├── output/                       # Documentos generados
├── requirements.txt
├── .env                          # API keys (no se sube a git)
└── .gitignore
```
