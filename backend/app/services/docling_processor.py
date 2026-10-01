import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    Servicio encargado de ingerir documentos técnicos en formato PDF (manuales O&M, normativas).
    Debido a bloqueos silenciosos (deadlocks) del motor IBM Docling en contenedores aislados, 
    se prioriza el motor PyPDFium2 (LangChain) para garantizar la extracción de texto en segundos.
    La arquitectura original de Docling se preserva intacta como un motor de contingencia futuro.
    """

    def __init__(self):
        self.converter = None

    def _get_converter(self):
        """
        Importa e instancia el motor de conversión.
        """
        if self.converter is None:
            logger.info("Importando motor IBM Docling...")
            try:
                from docling.document_converter import DocumentConverter
                try:
                    from docling.datamodel.pipeline_options import PdfPipelineOptions
                    pipeline_options = PdfPipelineOptions()
                    pipeline_options.do_table_structure = True
                    pipeline_options.do_ocr = True
                    self.converter = DocumentConverter(pdf_pipeline_options=pipeline_options)
                    logger.info("IBM Docling inicializado con soporte OCR extendido.")
                except Exception as fallback_e:
                    logger.warning(f"Opciones avanzadas Docling no disponibles ({str(fallback_e)}). Usando base.")
                    self.converter = DocumentConverter()
            except Exception as e:
                logger.error(f"Fallo al inicializar Docling: {str(e)}")
                self.converter = None
        return self.converter

    async def process_pdf_to_markdown(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF almacenado localmente y retorna su representación en texto crudo.
        Se ejecuta PyPDFium2 como motor principal para evadir el deadlock. Docling queda relegado a fallback.
        """
        start_time = time.time()
        
        if not os.path.exists(file_path):
            logger.error(f"El archivo {file_path} no fue encontrado en el sistema de archivos.")
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        logger.info(f"Iniciando extracción estructural del documento: {file_path}")

        text_content = ""
        used_engine = ""

        try:
            # MOTOR PRINCIPAL: PyPDFium2Loader de LangChain (Alta velocidad y robustez en Docker)
            from langchain_community.document_loaders import PyPDFium2Loader
            logger.info("Usando motor de extracción de alto rendimiento (PyPDFium2)...")
            loader = PyPDFium2Loader(file_path)
            docs = loader.load()
            text_content = "\n\n".join([doc.page_content for doc in docs])
            used_engine = "langchain_pypdfium2"
            
        except Exception as pypdfium2_err:
            logger.error(f"Fallo en motor PyPDFium2: {str(pypdfium2_err)}. Intentando con motor original Docling...")
            
            try:
                # MOTOR SECUNDARIO: IBM Docling (Arquitectura estructural original)
                converter = self._get_converter()
                
                if converter is None:
                    raise RuntimeError("El motor Docling no pudo inicializarse por fallos de dependencias.")
                    
                conversion_result = converter.convert(file_path)
                text_content = conversion_result.document.export_to_markdown()
                used_engine = "ibm_docling"
                
            except Exception as docling_err:
                logger.error(f"Fallo en motor Docling: {str(docling_err)}. Intentando con PyPDFLoader...")
                
                try:
                    # MOTOR DE CONTINGENCIA FINAL: PyPDFLoader (Motor universal puro Python)
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    text_content = "\n\n".join([doc.page_content for doc in docs])
                    used_engine = "langchain_pypdf"
                except Exception as final_err:
                    end_time = time.time()
                    logger.error(f"Fallo total en extracción: {str(final_err)}")
                    return {
                        "status": "error",
                        "filename": Path(file_path).name,
                        "error_message": f"Fallo en todos los motores de extracción. Último error: {str(final_err)}",
                        "processing_time_seconds": round(end_time - start_time, 2)
                    }

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        if not text_content or not text_content.strip():
            return {
                "status": "error",
                "filename": Path(file_path).name,
                "error_message": "El motor no encontró texto extraíble (posible PDF escaneado sin OCR).",
                "processing_time_seconds": processing_time
            }
            
        logger.info(f"Documento procesado exitosamente por {used_engine} en {processing_time} segundos.")
        
        return {
            "status": "success",
            "filename": Path(file_path).name,
            "markdown_content": text_content,
            "processing_time_seconds": processing_time,
            "metadata": {
                "source_type": "theoretical_manual",
                "original_format": "application/pdf",
                "conversion_engine": used_engine
            }
        }

    def save_markdown_to_disk(self, markdown_content: str, output_path: str) -> bool:
        """
        Utilidad para guardar el Markdown generado en el disco duro.
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(markdown_content)
            logger.info(f"Archivo Markdown exportado exitosamente en: {output_path}")
            return True
        except IOError as e:
            logger.error(f"Error de E/S al escribir el archivo Markdown en {output_path}: {str(e)}")
            return False

docling_service = DoclingProcessor()