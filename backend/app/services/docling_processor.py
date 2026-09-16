import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Importación de la librería principal de IBM Docling
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    Servicio encargado de ingerir documentos técnicos en formato PDF (manuales O&M, normativas)
    y decodificarlos estructuralmente a formato Markdown utilizando IBM Docling, 
    preservando la integridad de las tablas fisicoquímicas y la jerarquía de títulos.
    """

    def __init__(self):
        # Configuración de las opciones del pipeline para PDFs
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.do_ocr = True
        
        # Inicialización del convertidor de documentos
        try:
            self.converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                # Se pueden inyectar las opciones de pipeline aquí dependiendo de la versión de docling
            )
            logger.info("IBM Docling DocumentConverter inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error crítico al inicializar Docling: {str(e)}")
            raise e

    async def process_pdf_to_markdown(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF almacenado localmente y retorna su representación en Markdown.
        
        Args:
            file_path (str): Ruta absoluta o relativa al archivo PDF.
            
        Returns:
            Dict[str, Any]: Diccionario con el contenido estructurado y metadatos del procesamiento.
        """
        start_time = time.time()
        
        if not os.path.exists(file_path):
            logger.error(f"El archivo {file_path} no fue encontrado en el sistema de archivos.")
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        logger.info(f"Iniciando decodificación estructural del documento: {file_path}")

        try:
            # La conversión en Docling puede ser un proceso bloqueante pesado.
            # En un entorno de producción estricto con FastAPI, esto podría envolverse en run_in_threadpool
            conversion_result = self.converter.convert(file_path)
            
            # Exportar el documento decodificado a formato Markdown
            markdown_content = conversion_result.document.export_to_markdown()
            
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            
            logger.info(f"Documento procesado exitosamente en {processing_time} segundos.")
            
            return {
                "status": "success",
                "filename": Path(file_path).name,
                "markdown_content": markdown_content,
                "processing_time_seconds": processing_time,
                "metadata": {
                    "source_type": "theoretical_manual",
                    "original_format": "application/pdf",
                    "conversion_engine": "ibm_docling"
                }
            }

        except Exception as e:
            end_time = time.time()
            logger.error(f"Fallo durante la conversión del documento {file_path}. Error: {str(e)}")
            return {
                "status": "error",
                "filename": Path(file_path).name,
                "error_message": str(e),
                "processing_time_seconds": round(end_time - start_time, 2)
            }

    def save_markdown_to_disk(self, markdown_content: str, output_path: str) -> bool:
        """
        Utilidad para guardar el Markdown generado en el disco duro, útil para
        auditoría manual antes de pasarlo al Chunking.
        
        Args:
            markdown_content (str): El texto estructurado en Markdown.
            output_path (str): Ruta de destino para el archivo .md
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(markdown_content)
            logger.info(f"Archivo Markdown exportado exitosamente en: {output_path}")
            return True
        except IOError as e:
            logger.error(f"Error de E/S al escribir el archivo Markdown en {output_path}: {str(e)}")
            return False

# Instancia global del procesador para ser importada por los controladores (Singleton pattern)
docling_service = DoclingProcessor()