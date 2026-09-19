import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from app.core.config import engine
from app.services.docling_processor import docling_service

router = APIRouter()
logger = logging.getLogger(__name__)

class EmpiricalCaseCreate(BaseModel):
    author: str
    symptoms: str
    action_taken: str
    result: str

class EmpiricalCaseUpdate(BaseModel):
    author: str
    symptoms: str
    action_taken: str
    result: str

class EmpiricalCaseResponse(BaseModel):
    id: int
    status: str
    message: str

class ManualUploadResponse(BaseModel):
    status: str
    processing_time_seconds: float
    chunks_created: int

_embedder_instance = None

def get_embedding(text_input: str) -> list:
    global _embedder_instance
    if _embedder_instance is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Inicializando SentenceTransformer para rutas de la API...")
        _embedder_instance = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder_instance.encode(text_input).tolist()

@router.post("/empirical-case", response_model=EmpiricalCaseResponse)
async def create_empirical_case(case: EmpiricalCaseCreate):
    """
    Ingesta de conocimiento tácito (CBR).
    Recibe los datos del operario, los vectoriza y los almacena en PostgreSQL.
    """
    try:
        content_to_vectorize = f"SINTOMAS: {case.symptoms}\nACCION: {case.action_taken}\nRESULTADO: {case.result}"
        vector = get_embedding(content_to_vectorize)
        vector_str = str(vector)

        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO knowledge_vectors (author, symptoms, action_taken, result, content, source_type, embedding)
                    VALUES (:author, :symptoms, :action_taken, :result, :content, 'empirical_case', :embedding)
                    RETURNING id;
                """),
                {
                    "author": case.author,
                    "symptoms": case.symptoms,
                    "action_taken": case.action_taken,
                    "result": case.result,
                    "content": content_to_vectorize,
                    "embedding": vector_str
                }
            )
            inserted_id = result.scalar()

        logger.info(f"Caso empírico insertado exitosamente con ID {inserted_id} por {case.author}")
        
        return EmpiricalCaseResponse(
            id=inserted_id,
            status="success",
            message="Caso indexado correctamente en el motor CBR."
        )

    except Exception as e:
        logger.error(f"Fallo en la inserción del caso CBR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/empirical-cases")
async def get_empirical_cases():
    """
    Recupera todos los casos empíricos almacenados para ser visualizados en el panel de configuración.
    """
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT id, author, symptoms, action_taken, result, created_at 
                FROM knowledge_vectors 
                WHERE source_type = 'empirical_case' 
                ORDER BY created_at DESC
            """)
            result = conn.execute(query).fetchall()
            
            cases = []
            for row in result:
                cases.append({
                    "id": row.id,
                    "author": row.author,
                    "symptoms": row.symptoms,
                    "action_taken": row.action_taken,
                    "result": row.result,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })
                
        return {"status": "success", "data": cases}
    except Exception as e:
        logger.error(f"Error al consultar casos empíricos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/empirical-cases/{case_id}")
async def update_empirical_case(case_id: int, case: EmpiricalCaseUpdate):
    """
    Actualiza un caso empírico existente. Obliga a recalcular el embedding vectorial
    para asegurar la coherencia semántica con el nuevo texto modificado.
    """
    try:
        content_to_vectorize = f"SINTOMAS: {case.symptoms}\nACCION: {case.action_taken}\nRESULTADO: {case.result}"
        vector = get_embedding(content_to_vectorize)
        vector_str = str(vector)

        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE knowledge_vectors 
                    SET author = :author, 
                        symptoms = :symptoms, 
                        action_taken = :action_taken, 
                        result = :result, 
                        content = :content, 
                        embedding = :embedding 
                    WHERE id = :id AND source_type = 'empirical_case'
                """),
                {
                    "id": case_id,
                    "author": case.author,
                    "symptoms": case.symptoms,
                    "action_taken": case.action_taken,
                    "result": case.result,
                    "content": content_to_vectorize,
                    "embedding": vector_str
                }
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Caso empírico no encontrado.")

        logger.info(f"Caso empírico ID {case_id} actualizado y re-vectorizado exitosamente.")
        return {"status": "success", "message": "Caso actualizado y re-vectorizado correctamente."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar caso empírico ID {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/empirical-cases/{case_id}")
async def delete_empirical_case(case_id: int):
    """
    Elimina permanentemente un caso empírico de la base de datos vectorial.
    """
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM knowledge_vectors WHERE id = :id AND source_type = 'empirical_case'"),
                {"id": case_id}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Caso empírico no encontrado.")

        logger.info(f"Caso empírico ID {case_id} eliminado exitosamente.")
        return {"status": "success", "message": "Caso eliminado correctamente."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar caso empírico ID {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-manual", response_model=ManualUploadResponse)
async def upload_manual_endpoint(file: UploadFile = File(...)):
    """
    Ingesta normativa (RAG).
    Procesa archivos PDF usando IBM Docling, genera fragmentos semánticos y los inserta en PostgreSQL.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe tener un formato PDF.")

    temp_file_path = f"/tmp/{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        docling_result = await docling_service.process_pdf_to_markdown(temp_file_path)
        
        if docling_result["status"] == "error":
            raise Exception(docling_result["error_message"])

        markdown_text = docling_result["markdown_content"]
        
        chunks = [chunk.strip() for chunk in markdown_text.split("\n\n") if len(chunk.strip()) > 50]
        
        inserted_chunks = 0
        with engine.begin() as conn:
            for chunk in chunks:
                vector = get_embedding(chunk)
                conn.execute(
                    text("""
                        INSERT INTO document_chunks (content, metadata, embedding)
                        VALUES (:content, :metadata, :embedding)
                    """),
                    {
                        "content": chunk,
                        "metadata": file.filename,
                        "embedding": str(vector)
                    }
                )
                inserted_chunks += 1

        return ManualUploadResponse(
            status="success",
            processing_time_seconds=docling_result["processing_time_seconds"],
            chunks_created=inserted_chunks
        )

    except Exception as e:
        logger.error(f"Error procesando manual normativo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)