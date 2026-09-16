import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configuración del registro de eventos para auditoría
logger = logging.getLogger(__name__)

# Definición de la cadena de conexión extrayendo las credenciales del entorno Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ptar_admin:ptar_secure_password@vector_db:5432/ptar_knowledge_base"
)

# Inicialización del motor SQLAlchemy y la fábrica de sesiones
try:
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Motor de base de datos relacional inicializado correctamente.")
except Exception as e:
    logger.error(f"Error crítico al conectar con el contenedor PostgreSQL: {str(e)}")
    raise e

def get_db():
    """
    Generador de dependencias para proveer sesiones de base de datos a los endpoints de FastAPI.
    Garantiza el cierre seguro de la conexión tras la transacción, previniendo fugas de memoria.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()