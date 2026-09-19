import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Las importaciones globales de IBM Docling han sido retiradas de la cabecera 
# para aislar el hilo principal de Uvicorn y aplicar inicialización diferida (Lazy Loading).

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    Servicio encargado de ingerir documentos técnicos en formato PDF (manuales O&M, normativas)
    y decodificarlos estructuralmente a formato Markdown utilizando IBM Docling, 
    preservando la integridad de las tablas fisicoquímicas y la jerarquía de títulos.
    """

    def __init__(self):
        # Inicialización en nulo del convertidor de documentos para proteger el servidor
        self.converter = None

    def _get_converter(self):
        """
        Importa e instancia el motor de conversión únicamente cuando se recibe el primer documento.
        Evade dependencias obsoletas como 'InputFormat' ajustándose a la API moderna de Docling.
        """
        if self.converter is None:
            logger.info("Importando motor IBM Docling y modelos en tiempo de ejecución...")
            try:
                from docling.document_converter import DocumentConverter
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                
                # Configuración de las opciones del pipeline para PDFs
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_table_structure = True
                pipeline_options.do_ocr = True
                
                # Inicialización del convertidor de documentos (soporta PDF de forma nativa)
                # Se omite allowed_formats=[InputFormat.PDF] para prevenir el ImportError de rutas obsoletas.
                self.converter = DocumentConverter()
                
                logger.info("IBM Docling DocumentConverter inicializado correctamente.")
            except Exception as e:
                logger.error(f"Error crítico al inicializar Docling: {str(e)}")
                raise e
        return self.converter

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
            # Invoca el método de importación diferida en tiempo real
            converter = self._get_converter()
            
            # La conversión en Docling puede ser un proceso bloqueante pesado.
            # En un entorno de producción estricto con FastAPI, esto podría envolverse en run_in_threadpool
            conversion_result = converter.convert(file_path)
            
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