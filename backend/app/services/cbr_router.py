import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sentence_transformers import SentenceTransformer
from app.models import KnowledgeVector

logger = logging.getLogger(__name__)

class CBRRouter:
    """
    Servicio encargado de la vectorización en memoria y el enrutamiento lógico 
    de las consultas, aplicando el filtrado de metadatos para separar la 
    experiencia empírica de la literatura normativa.
    """
    def __init__(self):
        logger.info("Inicializando modelo SentenceTransformers (CPU/GPU local)...")
        # Modelo multilingüe optimizado de 384 dimensiones.
        self.encoder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.embedding_dimension = 384
        logger.info("Modelo de vectorización SentenceTransformers cargado con éxito.")

    def embed_text(self, text: str) -> List[float]:
        """
        Transforma el texto en lenguaje natural a un vector denso.
        """
        vector = self.encoder.encode(text)
        return vector.tolist()

    def store_empirical_case(self, db: Session, symptoms: str, action: str, result: str, author: str) -> KnowledgeVector:
        """
        Estructura el reporte operativo de la bitácora, lo vectoriza y lo almacena 
        en la base de datos con el metadato 'empirical_case'.
        """
        content = f"SINTOMAS: {symptoms}\nACCION: {action}\nRESULTADO: {result}"
        vector = self.embed_text(content)

        new_case = KnowledgeVector(
            content=content,
            source_type="empirical_case",
            author=author,
            embedding=vector
        )
        
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        logger.info(f"Caso empírico insertado exitosamente con ID {new_case.id} por {author}")
        return new_case

    def store_theoretical_chunk(self, db: Session, chunk_content: str, filename: str) -> KnowledgeVector:
        """
        Vectoriza y almacena un fragmento de Markdown procesado por IBM Docling 
        con el metadato 'theoretical_manual'.
        """
        vector = self.embed_text(chunk_content)

        new_chunk = KnowledgeVector(
            content=chunk_content,
            source_type="theoretical_manual",
            author=filename,
            embedding=vector
        )
        
        db.add(new_chunk)
        db.commit()
        db.refresh(new_chunk)
        logger.info(f"Fragmento normativo insertado exitosamente con ID {new_chunk.id} (Origen: {filename})")
        return new_chunk

    def route_and_search(self, db: Session, query: str, similarity_threshold: float = 0.85) -> Dict[str, Any]:
        """
        Ejecuta la búsqueda de similitud secuencial. 
        Calcula la distancia del coseno utilizando la extensión pgvector en PostgreSQL.
        """
        query_vector = self.embed_text(query)
        distance_threshold = 1.0 - similarity_threshold

        # Paso A: Búsqueda estricta en Bitácora Empírica (CBR)
        empirical_query = select(
            KnowledgeVector, 
            KnowledgeVector.embedding.cosine_distance(query_vector).label("distance")
        ).where(KnowledgeVector.source_type == "empirical_case").order_by("distance").limit(3)
        
        empirical_results = db.execute(empirical_query).all()
        
        valid_empirical = [row for row in empirical_results if row.distance <= distance_threshold]
        
        if valid_empirical:
            logger.info("Caso empírico detectado. Enrutando hacia estrategia CBR.")
            return {
                "routing_strategy": "CBR",
                "documents": [
                    {
                        "content": row.KnowledgeVector.content, 
                        "author": row.KnowledgeVector.author, 
                        "similarity": round(1.0 - row.distance, 4)
                    } for row in valid_empirical
                ]
            }
        
        # Paso B: Fallback a Manuales Normativos (RAG) si no hay casos empíricos similares
        logger.info("Sin casos empíricos suficientes. Ejecutando fallback teórico RAG.")
        theoretical_query = select(
            KnowledgeVector, 
            KnowledgeVector.embedding.cosine_distance(query_vector).label("distance")
        ).where(KnowledgeVector.source_type == "theoretical_manual").order_by("distance").limit(3)
            
        theoretical_results = db.execute(theoretical_query).all()
        
        # Para la literatura teórica somos más permisivos con el umbral (ej. ampliamos la tolerancia de distancia)
        valid_theoretical = [row for row in theoretical_results if row.distance <= (distance_threshold + 0.15)]

        return {
            "routing_strategy": "RAG",
            "documents": [
                {
                    "content": row.KnowledgeVector.content, 
                    "author": row.KnowledgeVector.author, 
                    "similarity": round(1.0 - row.distance, 4)
                } for row in valid_theoretical
            ]
        }

# Instancia global del enrutador
cbr_service = CBRRouter()