"""
Servicio para generar documentos Word (.docx) a partir de una plantilla
usando docxtpl (Jinja2 para Word).
"""

import os
import logging
from datetime import datetime
from docxtpl import DocxTemplate

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        # Asegurarnos que la carpeta de output existe
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Primero buscamos la plantilla preparada (plantilla_jinja.docx)
        self.template_path = settings.TEMPLATES_DIR / "plantilla_jinja.docx"
        
        # Si no existe, usamos la original, pero advertimos (porque fallará si no tiene tags Jinja)
        if not self.template_path.exists():
            original = settings.TEMPLATES_DIR / "plantilla_historia_clinica.docx"
            if original.exists():
                logger.warning(f"No se encontró {self.template_path}, usando original {original}")
                self.template_path = original
            else:
                logger.error("No se encontró ninguna plantilla en la carpeta templates/")

    def generar_documento(self, datos_clinicos: dict, sesion_id: int) -> str:
        """
        Toma el diccionario de datos clínicos (extraído por Gemini) 
        y lo inyecta en la plantilla Word, creando una copia en output/.
        Retorna la ruta absoluta del nuevo archivo generado.
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"Plantilla no encontrada: {self.template_path}")

        try:
            logger.info(f"Cargando plantilla desde {self.template_path}")
            doc = DocxTemplate(str(self.template_path))
            
            # El contexto es directamente el diccionario devuelto por Gemini.
            # En la plantilla, accederemos a los campos como:
            # {{ informacion_paciente.nombre }}
            # {{ historia_personal.historia_familiar }}
            contexto = datos_clinicos
            
            # Agregamos algunos campos extra útiles que no vienen de Gemini
            contexto["fecha_generacion"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            contexto["sesion_id"] = sesion_id
            
            # Agregamos los datos del profesional para la firma final
            # (En el futuro, esto puede venir del usuario logueado en la app)
            contexto["profesional"] = {
                "nombre": "Dr. Angel (Psicólogo Clínico)",
                "tarjeta_profesional": "123456-TP"
            }

            # Renderizar el documento con los datos
            doc.render(contexto)
            
            # Crear un nombre único para el archivo
            nombre_paciente = datos_clinicos.get("informacion_paciente", {}).get("nombre", "Paciente")
            apellidos = datos_clinicos.get("informacion_paciente", {}).get("apellidos", "")
            
            # Limpiar nombre para nombre de archivo
            nombre_archivo = f"Historia_{nombre_paciente}_{apellidos}_{sesion_id}.docx".replace(" ", "_")
            
            ruta_salida = self.output_dir / nombre_archivo
            
            # Guardar el documento
            doc.save(str(ruta_salida))
            logger.info(f"✅ Documento generado con éxito: {ruta_salida}")
            
            return str(ruta_salida)

        except Exception as e:
            logger.error(f"Error generando documento Word: {e}")
            raise
