from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.config import Base

class KnowledgeVector(Base):
    """
    Modelo ORM Unificado para la Bitácora Empírica (CBR) y búsqueda RAG.
    Consolida las columnas requeridas por el enrutador lógico y los endpoints de inserción.
    """
    __tablename__ = "knowledge_vectors"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Columnas base para la inferencia híbrida y enrutamiento en cbr_router.py
    content = Column(Text, nullable=False, doc="Contenido en texto crudo (caso empírico o chunk de docling)")
    source_type = Column(String(50), nullable=False, index=True, doc="Filtro estricto: 'empirical_case' o 'theoretical_manual'")
    author = Column(String(255), nullable=True, doc="Identificador del operario o nombre del archivo origen")
    
    # Columnas específicas para el desglose mapeado en el panel de configuración Vue
    symptoms = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), doc="Marca de tiempo de la indexación")
    
    # Dimensiones explícitas requeridas por el motor SentenceTransformer
    embedding = Column(Vector(384), nullable=False)

class DocumentChunk(Base):
    """
    Modelo ORM para la Ingesta Normativa (Generación Aumentada por Recuperación - RAG).
    Almacena los fragmentos de los manuales procesados por IBM Docling.
    """
    __tablename__ = "document_chunks"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # Se evade la palabra reservada 'metadata' en el ORM de Python
    doc_metadata = Column("metadata", String(255), nullable=False)
    
    # Dimensiones explícitas requeridas por el motor SentenceTransformer
    embedding = Column(Vector(384))