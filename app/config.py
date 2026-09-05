"""
Configuración centralizada del proyecto.
Carga variables de entorno desde .env y las expone como un objeto tipado.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Directorio raíz del proyecto (donde está el .env)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Todas las configuraciones del proyecto en un solo lugar.
    pydantic-settings lee automáticamente del archivo .env
    """

    # ── API Keys ──────────────────────────────────────────
    DEEPGRAM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Rutas del proyecto ────────────────────────────────
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    STATIC_DIR: Path = BASE_DIR / "static"
    DB_PATH: Path = BASE_DIR / "asistente.db"

    # ── Nombre del archivo de plantilla ───────────────────
    TEMPLATE_FILENAME: str = "plantilla_historia_clinica.docx"

    # ── Configuración de audio ────────────────────────────
    AUDIO_SAMPLE_RATE: int = 16000  # 16kHz — estándar para STT
    AUDIO_CHANNELS: int = 1        # 1=mono (diarización), 2=estéreo (multicanal)

    # ── Deepgram ──────────────────────────────────────────
    DEEPGRAM_MODEL: str = "nova-3"
    DEEPGRAM_LANGUAGE: str = "es"   # Español

    # ── Gemini ────────────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Servidor ──────────────────────────────────────────
    APP_TITLE: str = "Asistente IA - Psicología Clínica"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # Ignorar variables de entorno no definidas aquí
    )


# Instancia global — se importa desde cualquier parte del proyecto
# Ejemplo: from app.config import settings
settings = Settings()
