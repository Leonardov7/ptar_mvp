from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# ESQUEMAS PARA LA BITÁCORA EMPÍRICA (CBR)
# ==========================================

class EmpiricalCaseBase(BaseModel):
    """
    Estructura base de un caso operativo reportado por el personal de planta.
    Captura los síntomas del reactor, la acción ejecutada y el resultado obtenido.
    """
    symptoms: str = Field(
        ..., 
        description="Descripción del problema, ej: DBO5 alta, lodo flotante, olor séptico."
    )
    action_taken: str = Field(
        ..., 
        description="Acción heurística realizada, ej: Aumento de purga, cierre de válvulas."
    )
    result: str = Field(
        ..., 
        description="Resultado de la acción, ej: Estabilización del manto de lodos en 2 horas."
    )
    author: str = Field(
        ..., 
        description="Nombre o identificador del operario que documenta el caso."
    )

class EmpiricalCaseCreate(EmpiricalCaseBase):
    """
    Esquema utilizado para la creación y recepción de datos desde el Frontend.
    """
    pass

class EmpiricalCaseResponse(EmpiricalCaseBase):
    """
    Esquema de respuesta tras la vectorización e indexación exitosa del caso.
    """
    id: int
    created_at: datetime
    source_type: str = "empirical_case"

    class Config:
        from_attributes = True

# ==========================================
# ESQUEMAS PARA LAS CONSULTAS (RAG / CBR)
# ==========================================

class QueryRequest(BaseModel):
    """
    Estructura de la consulta enviada por el usuario a través del chat.
    Incluye el perfil del usuario para el ecualizador de personalidad.
    """
    query: str = Field(
        ..., 
        description="Pregunta en lenguaje natural sobre un problema operativo o normativo."
    )
    user_profile: str = Field(
        default="operator", 
        description="Perfil del usuario (ej: 'operator', 'engineer') para ajustar el System Prompt."
    )
    similarity_threshold: Optional[float] = Field(
        default=0.85, 
        description="Umbral de similitud del coseno para decidir entre CBR y RAG."
    )

class SourceDocument(BaseModel):
    """
    Estructura de los fragmentos de texto recuperados de la base de datos vectorial.
    """
    content: str
    source_type: str # 'empirical_case' o 'theoretical_manual'
    metadata: dict
    similarity_score: float

class QueryResponse(BaseModel):
    """
    Respuesta final generada por el LLM junto con las fuentes utilizadas.
    """
    answer: str = Field(
        ..., 
        description="Texto generado por Ollama (Llama 3 / Mistral)."
    )
    primary_source_type: str = Field(
        ..., 
        description="Indica si la respuesta se basó en la bitácora (CBR) o en los manuales (RAG)."
    )
    sources: List[SourceDocument] = Field(
        default=[], 
        description="Lista de documentos recuperados que fundamentan la respuesta."
    )

# ==========================================
# ESQUEMAS PARA LA INGESTA DE DOCUMENTOS
# ==========================================

class DocumentUploadResponse(BaseModel):
    """
    Respuesta tras procesar un manual de la PTAR con IBM Docling.
    """
    filename: str
    status: str
    chunks_created: int
    processing_time_seconds: float