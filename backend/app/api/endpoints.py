import os
import shutil
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_text_splitters import MarkdownHeaderTextSplitter

from app.core.config import get_db
from app.models.schemas import (
    EmpiricalCaseCreate, 
    EmpiricalCaseResponse, 
    QueryRequest, 
    QueryResponse, 
    DocumentUploadResponse
)
from app.services.docling_processor import docling_service
from app.services.cbr_router import cbr_service
from app.services.rag_engine import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuración de los divisores de texto de LangChain
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

@router.post("/upload-manual", response_model=DocumentUploadResponse, tags=["RAG Document Ingestion"])
async def upload_theoretical_manual(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Ingesta de documentos teóricos. Guarda el PDF temporalmente, lo procesa con 
    IBM Docling, fragmenta el Markdown resultante e indexa los vectores en PostgreSQL.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El sistema solo admite archivos PDF.")

    temp_path = f"/tmp/{file.filename}"
    try:
        # Guardar archivo en almacenamiento temporal del contenedor
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Procesamiento Estructural (Visión Computacional a Markdown)
        docling_result = await docling_service.process_pdf_to_markdown(temp_path)
        if docling_result["status"] == "error":
            raise HTTPException(status_code=500, detail=docling_result["error_message"])
            
        md_content = docling_result["markdown_content"]
        
        # 2. Fragmentación Semántica (Chunking)
        md_header_splits = markdown_splitter.split_text(md_content)
        chunks_created = len(md_header_splits)
        
        # 3. Vectorización e Inserción en la Base de Datos
        for chunk in md_header_splits:
            # Reconstruir el chunk incluyendo sus metadatos estructurales
            headers = " > ".join([v for k, v in chunk.metadata.items()])
            structured_text = f"[{headers}]\n{chunk.page_content}" if headers else chunk.page_content
            
            cbr_service.store_theoretical_chunk(
                db=db, 
                chunk_content=structured_text, 
                filename=file.filename
            )
            
        return DocumentUploadResponse(
            filename=file.filename,
            status="success",
            chunks_created=chunks_created,
            processing_time_seconds=docling_result["processing_time_seconds"]
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/empirical-case", response_model=EmpiricalCaseResponse, tags=["CBR Empirical Logging"])
def create_empirical_case(case: EmpiricalCaseCreate, db: Session = Depends(get_db)):
    """
    Recibe el formulario de la bitácora desde el Frontend, lo vectoriza
    y lo almacena como caso de estudio empírico.
    """
    try:
        db_case = cbr_service.store_empirical_case(
            db=db,
            symptoms=case.symptoms,
            action=case.action_taken,
            result=case.result,
            author=case.author
        )
        return db_case
    except Exception as e:
        logger.error(f"Fallo al indexar caso empírico: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al vectorizar el caso.")

@router.post("/chat/sync", response_model=QueryResponse, tags=["Inference"])
def synchronous_chat(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Inferencia tradicional (bloqueante). Útil para pruebas de API, aunque para el 
    frontend se utilizará el WebSocket para evitar el TTFT alto.
    """
    # 1. Enrutamiento CBR vs RAG
    routing_data = cbr_service.route_and_search(
        db=db, 
        query=request.query, 
        similarity_threshold=request.similarity_threshold
    )
    
    # 2. Generación LLM
    response_data = rag_service.generate_response(
        query=request.query,
        routing_strategy=routing_data["routing_strategy"],
        documents=routing_data["documents"],
        user_profile=request.user_profile
    )
    
    return QueryResponse(**response_data)