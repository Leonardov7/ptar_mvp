import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import engine, Base

# Importación absoluta para garantizar el registro del esquema en Base.metadata
import app.models

from app.api.endpoints import router as api_router
from app.api.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando orquestador. Verificando conexión a PostgreSQL...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Extensión pgvector verificada en PostgreSQL.")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Estructura de tablas ORM sincronizada.")
    except Exception as e:
        logger.error(f"Error crítico de base de datos en el arranque: {str(e)}")
    
    yield 
    
    logger.info("Apagando orquestador y liberando recursos.")

app = FastAPI(
    title="API Híbrida RAG y CBR - PTAR",
    description="Backend para el sistema de soporte a la decisión basado en casos empíricos y normatividad ambiental.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "service": "PTAR MVP API",
        "message": "El orquestador backend está en funcionamiento y el puerto 8000 está abierto."
    }