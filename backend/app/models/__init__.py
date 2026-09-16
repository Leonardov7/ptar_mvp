from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.config import Base

class KnowledgeVector(Base):
    """
    Entidad ORM (Object-Relational Mapping) que representa la base de conocimiento unificada.
    Almacena tanto la bitácora empírica (CBR) como los manuales teóricos (RAG), diferenciados
    exclusivamente por la columna 'source_type'.
    """
    __tablename__ = "knowledge_vectors"

    id = Column(Integer, primary_key=True, index=True)
    
    content = Column(
        Text, 
        nullable=False, 
        doc="Contenido en texto crudo (caso empírico o chunk de docling)"
    )
    
    source_type = Column(
        String(50), 
        nullable=False, 
        index=True, 
        doc="Filtro estricto: 'empirical_case' o 'theoretical_manual'"
    )
    
    author = Column(
        String(100), 
        nullable=True, 
        doc="Identificador del operario o nombre del archivo origen"
    )
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        doc="Marca de tiempo de la indexación"
    )
    
    # Columna vectorial dimensionada para paraphrase-multilingual-MiniLM-L12-v2
    embedding = Column(
        Vector(384), 
        nullable=False, 
        doc="Representación matemática del texto en el espacio latente"
    )