import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# 4. Inclusión de rutas modulares (AHORA DESCOMENTADAS)
from app.api.endpoints import router as api_router
from app.api.websocket import router as ws_router

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")


# Importación de enrutadores modulares (Se descomentarán cuando se creen los archivos de rutas)
# from app.api.endpoints import router as api_router
# from app.api.websocket import router as ws_router

# 1. Configuración del registro de eventos (Logging) para depuración en Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 2. Inicialización de la aplicación FastAPI
app = FastAPI(
    title="API Híbrida RAG y CBR - PTAR",
    description="Backend para el sistema de soporte a la decisión basado en casos empíricos y normatividad ambiental.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 3. Configuración de CORS para permitir la comunicación cruzada entre contenedores
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Inclusión de rutas modulares (Comentadas temporalmente)
# app.include_router(api_router, prefix="/api/v1")
# app.include_router(ws_router, prefix="/ws/v1")

# 5. Endpoint raíz para comprobación de estado de los servicios
@app.get("/", tags=["Health Check"])
async def root():
    """
    Endpoint de comprobación de salud para el balanceador o contenedor.
    """
    logger.info("Comprobación de estado de la API solicitada.")
    return {
        "status": "online",
        "service": "PTAR MVP API",
        "message": "El orquestador backend está en funcionamiento y listo para recibir peticiones."
    }