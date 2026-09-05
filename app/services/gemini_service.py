"""
Servicio LLM usando Google Gemini 2.5 Flash para extraer los datos
clínicos desde la transcripción de la sesión.
"""

import logging
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import HistoriaClinicaCompleta

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        # Inicializa el cliente con la API key
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.modelo = settings.GEMINI_MODEL  # ej. "gemini-2.5-flash"

    async def extraer_datos_clinicos(self, transcripcion: str) -> dict:
        """
        Envía la transcripción al LLM y le pide que extraiga la información
        exactamente con el esquema Pydantic de HistoriaClinicaCompleta.
        """
        if not transcripcion or len(transcripcion.strip()) < 10:
            logger.warning("Transcripción demasiado corta para extraer datos.")
            # Retorna un diccionario vacío con los campos por defecto ("No mencionado")
            return HistoriaClinicaCompleta().model_dump()

        prompt = f"""
        Eres un asistente experto en psicología clínica. 
        Tu objetivo es leer la siguiente transcripción de una sesión terapéutica
        y extraer toda la información relevante para rellenar una historia clínica completa.
        
        Si una información NO se menciona en la sesión, pon estrictamente "No mencionado".
        Resume y redacta en tono profesional y clínico.

        Transcripción de la sesión:
        -----------------------------
        {transcripcion}
        """

        logger.info("Enviando transcripción a Gemini para extracción de datos...")

        try:
            # Usar Structured Outputs obligando al modelo a devolver JSON
            # que cumpla con nuestro esquema de HistoriaClinicaCompleta
            response = self.client.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=HistoriaClinicaCompleta,
                    temperature=0.2, # Baja temperatura para mayor precisión y consistencia
                ),
            )

            # Gemini devuelve un JSON válido como texto
            resultado_json = response.text
            
            # Validar que el JSON encaja en nuestro modelo Pydantic
            historia_validada = HistoriaClinicaCompleta.model_validate_json(resultado_json)
            
            logger.info("Extracción completada con éxito.")
            return historia_validada.model_dump()

        except ValidationError as e:
            logger.error(f"Error de validación del esquema devuelto por Gemini: {e}")
            raise
        except Exception as e:
            logger.error(f"Error llamando a la API de Gemini: {e}")
            raise
