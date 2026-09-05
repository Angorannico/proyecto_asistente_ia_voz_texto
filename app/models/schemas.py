"""
Schemas Pydantic para los datos clínicos de la historia clínica.

Estos modelos cumplen tres funciones:
1. Definen la estructura del JSON que Gemini debe devolver.
2. Validan automáticamente que el JSON sea correcto.
3. Sirven como contrato entre el LLM, el backend y la plantilla Word.

Cada clase corresponde a una sección de la plantilla
'plantilla_historia_clinica.docx'.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 1: Información del Paciente
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class InformacionPaciente(BaseModel):
    """Datos personales del paciente extraídos de la conversación."""

    nombre: str = Field(
        default="No mencionado",
        description="Nombre(s) del paciente"
    )
    apellidos: str = Field(
        default="No mencionado",
        description="Apellido(s) del paciente"
    )
    dni: str = Field(
        default="No mencionado",
        description="Documento de identidad (cédula, DNI, etc.)"
    )
    direccion: str = Field(
        default="No mencionado",
        description="Dirección de residencia"
    )
    correo: str = Field(
        default="No mencionado",
        description="Correo electrónico"
    )
    celular: str = Field(
        default="No mencionado",
        description="Número de celular o teléfono"
    )
    nacimiento: str = Field(
        default="No mencionado",
        description="Fecha de nacimiento"
    )
    ciudad: str = Field(
        default="No mencionado",
        description="Ciudad de residencia"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 2: Motivo de Consulta
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Es un campo simple (str), se incluye directamente en HistoriaClinicaCompleta.


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 3: Problema Actual
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProblemaActual(BaseModel):
    """Descripción detallada de la problemática actual del paciente."""

    inicio_malestar: str = Field(
        default="No mencionado",
        description="Cuándo comenzó el malestar y circunstancias iniciales"
    )
    evolucion: str = Field(
        default="No mencionado",
        description="Cómo ha evolucionado el problema desde su inicio"
    )
    frecuencia_intensidad: str = Field(
        default="No mencionado",
        description="Con qué frecuencia ocurre y qué tan intenso es"
    )
    situaciones_desencadenantes: str = Field(
        default="No mencionado",
        description="Situaciones, personas o contextos que desencadenan o agravan el problema"
    )
    estrategias_intentadas: str = Field(
        default="No mencionado",
        description="Qué ha intentado el paciente para manejar el problema"
    )
    impacto_areas_vida: str = Field(
        default="No mencionado",
        description="Cómo afecta el problema en lo personal, social y laboral"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 4: Historia Personal Relevante
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HistoriaPersonal(BaseModel):
    """Antecedentes relevantes de la historia de vida del paciente."""

    antecedentes_psicologicos: str = Field(
        default="No mencionado",
        description="Historial de tratamientos psicológicos o psiquiátricos previos"
    )
    historia_medica: str = Field(
        default="No mencionado",
        description="Condiciones médicas relevantes, medicamentos actuales"
    )
    eventos_significativos: str = Field(
        default="No mencionado",
        description="Pérdidas, cambios, traumas o experiencias marcantes"
    )
    historia_vincular: str = Field(
        default="No mencionado",
        description="Relaciones importantes en la historia del paciente"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 5: Contexto Actual
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ContextoActual(BaseModel):
    """Situación actual del entorno del paciente."""

    relaciones_significativas: str = Field(
        default="No mencionado",
        description="Relaciones significativas actuales del paciente"
    )
    dinamica_familiar: str = Field(
        default="No mencionado",
        description="Cómo es la dinámica familiar actual"
    )
    red_apoyo: str = Field(
        default="No mencionado",
        description="Personas o grupos que sirven de apoyo"
    )
    situacion_laboral: str = Field(
        default="No mencionado",
        description="Situación laboral o académica actual"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 6: Funcionamiento Psicológico Actual
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class FuncionamientoPsicologico(BaseModel):
    """Estado psicológico actual observado y reportado."""

    estado_animo: str = Field(
        default="No mencionado",
        description="Estado de ánimo predominante del paciente"
    )
    regulacion_emocional: str = Field(
        default="No mencionado",
        description="Capacidad del paciente para regular sus emociones"
    )
    estilo_pensamiento: str = Field(
        default="No mencionado",
        description="Patrones de pensamiento: rumiación, rigidez, catastrofismo, etc."
    )
    conductas_relevantes: str = Field(
        default="No mencionado",
        description="Conductas problemáticas: evitación, impulsividad, aislamiento, etc."
    )
    patrones_relacionales: str = Field(
        default="No mencionado",
        description="Patrones observables en las relaciones del paciente"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 7: Recursos y Fortalezas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class RecursosFortalezas(BaseModel):
    """Recursos internos y externos del paciente."""

    capacidades_personales: str = Field(
        default="No mencionado",
        description="Habilidades y fortalezas personales del paciente"
    )
    estrategias_afrontamiento: str = Field(
        default="No mencionado",
        description="Estrategias de afrontamiento funcionales que ya utiliza"
    )
    apoyos_disponibles: str = Field(
        default="No mencionado",
        description="Recursos y apoyos externos disponibles"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 8: Evaluación de Riesgo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EvaluacionRiesgo(BaseModel):
    """Evaluación de factores de riesgo del paciente."""

    ideacion_suicida: str = Field(
        default="No mencionado",
        description="Presencia de ideación suicida actual o pasada"
    )
    conductas_autolesivas: str = Field(
        default="No mencionado",
        description="Historial o presencia de conductas autolesivas"
    )
    consumo_sustancias: str = Field(
        default="No mencionado",
        description="Consumo de alcohol, drogas u otras sustancias"
    )
    riesgo: str = Field(
        default="No mencionado",
        description="Valoración general del riesgo para sí mismo u otros"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 9: Hipótesis Clínica Inicial
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HipotesisClinica(BaseModel):
    """Hipótesis clínica inicial del psicólogo."""

    comprension_caso: str = Field(
        default="No mencionado",
        description="Comprensión global de qué puede estar pasando con el paciente"
    )
    factores_mantenedores: str = Field(
        default="No mencionado",
        description="Factores que mantienen o perpetúan el problema"
    )
    posibles_patrones: str = Field(
        default="No mencionado",
        description="Patrones emocionales, cognitivos o relacionales identificados"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 10: Objetivos Terapéuticos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ObjetivosTerapeuticos(BaseModel):
    """Objetivos del proceso terapéutico."""

    expectativas_paciente: str = Field(
        default="No mencionado",
        description="Qué espera el paciente del proceso terapéutico"
    )
    necesidades_trabajo: str = Field(
        default="No mencionado",
        description="Qué considera el psicólogo necesario trabajar"
    )
    priorizacion_objetivos: str = Field(
        default="No mencionado",
        description="Orden de prioridad de los objetivos terapéuticos"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 11: Plan de Intervención Inicial
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class PlanIntervencion(BaseModel):
    """Plan de intervención terapéutica propuesto."""

    frecuencia_sugerida: str = Field(
        default="No mencionado",
        description="Frecuencia sugerida de las sesiones (semanal, quincenal, etc.)"
    )
    tipo_abordaje: str = Field(
        default="No mencionado",
        description="Enfoque o tipo de terapia propuesto (TCC, psicodinámica, humanista, etc.)"
    )
    primeras_lineas: str = Field(
        default="No mencionado",
        description="Primeras líneas de trabajo a implementar"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECCIÓN 12: Observaciones Clínicas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ObservacionesClinicas(BaseModel):
    """Observaciones adicionales del psicólogo sobre la sesión."""

    actitud_proceso: str = Field(
        default="No mencionado",
        description="Actitud del paciente frente al proceso terapéutico"
    )
    nivel_insight: str = Field(
        default="No mencionado",
        description="Nivel de consciencia del paciente sobre su situación"
    )
    aspectos_adicionales: str = Field(
        default="No mencionado",
        description="Cualquier aspecto relevante no registrado en las secciones anteriores"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEMA RAÍZ: Historia Clínica Completa
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HistoriaClinicaCompleta(BaseModel):
    """
    Schema raíz que agrupa TODAS las secciones de la historia clínica.
    Este es el modelo que Gemini debe devolver como JSON.
    """

    informacion_paciente: InformacionPaciente = Field(
        default_factory=InformacionPaciente,
        description="Datos personales del paciente"
    )
    motivo_consulta: str = Field(
        default="No mencionado",
        description="Motivo principal por el que el paciente acude a consulta"
    )
    problema_actual: ProblemaActual = Field(
        default_factory=ProblemaActual,
        description="Descripción del problema actual"
    )
    historia_personal: HistoriaPersonal = Field(
        default_factory=HistoriaPersonal,
        description="Historia personal relevante"
    )
    contexto_actual: ContextoActual = Field(
        default_factory=ContextoActual,
        description="Contexto actual del paciente"
    )
    funcionamiento_psicologico: FuncionamientoPsicologico = Field(
        default_factory=FuncionamientoPsicologico,
        description="Funcionamiento psicológico actual"
    )
    recursos_fortalezas: RecursosFortalezas = Field(
        default_factory=RecursosFortalezas,
        description="Recursos y fortalezas del paciente"
    )
    evaluacion_riesgo: EvaluacionRiesgo = Field(
        default_factory=EvaluacionRiesgo,
        description="Evaluación de riesgo"
    )
    hipotesis_clinica: HipotesisClinica = Field(
        default_factory=HipotesisClinica,
        description="Hipótesis clínica inicial"
    )
    objetivos_terapeuticos: ObjetivosTerapeuticos = Field(
        default_factory=ObjetivosTerapeuticos,
        description="Objetivos del proceso terapéutico"
    )
    plan_intervencion: PlanIntervencion = Field(
        default_factory=PlanIntervencion,
        description="Plan de intervención inicial"
    )
    observaciones_clinicas: ObservacionesClinicas = Field(
        default_factory=ObservacionesClinicas,
        description="Observaciones clínicas adicionales"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATOS DEL PROFESIONAL (para la firma del documento)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DatosProfesional(BaseModel):
    """Datos del psicólogo para la firma del documento."""

    nombre_profesional: str = Field(
        default="",
        description="Nombre completo del profesional"
    )
    tp_profesional: str = Field(
        default="",
        description="Número de tarjeta profesional"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEMAS DE SESIÓN (para la API y base de datos)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SesionCreate(BaseModel):
    """Datos para crear una nueva sesión."""

    modo: str = Field(
        description="Modo de la sesión: 'virtual' o 'presencial'"
    )


class SesionResponse(BaseModel):
    """Datos de una sesión almacenada."""

    id: int
    fecha: datetime
    modo: str
    estado: str  # "grabando", "analizando", "completada", "error"
    ruta_documento: Optional[str] = None
