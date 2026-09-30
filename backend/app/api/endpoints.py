import os
import logging
from typing import List
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
    files_processed: int

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
async def upload_manual_endpoint(files: List[UploadFile] = File(...)):
    """
    Ingesta normativa (RAG) en lote.
    Procesa múltiples archivos PDF secuencialmente usando IBM Docling, genera fragmentos semánticos y los inserta.
    """
    total_chunks = 0
    total_time = 0.0
    files_processed = 0

    for file in files:
        if not file.filename.endswith('.pdf'):
            logger.warning(f"Archivo omitido por no ser PDF: {file.filename}")
            continue

        temp_file_path = f"/tmp/{file.filename}"
        
        try:
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            docling_result = await docling_service.process_pdf_to_markdown(temp_file_path)
            
            if docling_result["status"] == "error":
                logger.error(f"Fallo al decodificar {file.filename}: {docling_result.get('error_message')}")
                continue

            markdown_text = docling_result["markdown_content"]
            total_time += docling_result["processing_time_seconds"]
            
            chunks = [chunk.strip() for chunk in markdown_text.split("\n\n") if len(chunk.strip()) > 50]
            
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
                    total_chunks += 1
            
            files_processed += 1

        except Exception as e:
            logger.error(f"Excepción general procesando archivo {file.filename}: {str(e)}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    if files_processed == 0:
        raise HTTPException(status_code=500, detail="No se pudo extraer texto de ningún archivo proporcionado.")

    return ManualUploadResponse(
        status="success",
        processing_time_seconds=round(total_time, 2),
        chunks_created=total_chunks,
        files_processed=files_processed
    )