import os
import json
import logging
import requests
from typing import List, Dict, Any, Generator

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Motor de Inferencia LLM.
    Orquesta la comunicación con el contenedor de Ollama, inyecta el contexto recuperado 
    (RAG Teórico o CBR Empírico) y aplica el Ecualizador de Personalidad mediante System Prompts.
    """
    def __init__(self):
        # Captura las credenciales de red definidas en el docker-compose.yml
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://llm_engine:11434")
        self.model_name = os.getenv("LLM_MODEL_NAME", "llama3")
        self.api_endpoint = f"{self.ollama_url}/api/chat"
        logger.info(f"RAG Engine inicializado. Conectando al modelo {self.model_name} en {self.ollama_url}")

    def _build_context_string(self, documents: List[Dict[str, Any]]) -> str:
        """
        Formatea los documentos recuperados de PostgreSQL/pgvector en una cadena 
        estructurada para ser inyectada en la ventana de atención del LLM.
        """
        context = ""
        for idx, doc in enumerate(documents, 1):
            similarity = doc.get('similarity', 0)
            author = doc.get('author', 'Desconocido')
            context += f"\n--- DOCUMENTO {idx} (Origen: {author} | Similitud: {similarity}) ---\n"
            context += f"{doc.get('content', '')}\n"
        return context

    def _get_system_prompt(self, routing_strategy: str, user_profile: str, context: str) -> str:
        """
        ECUALIZADOR DE PERSONALIDAD:
        Ajusta el tono, la terminología y las instrucciones base del LLM dependiendo 
        de la fuente (empírica vs teórica) y del rol del usuario (operario vs ingeniero).
        """
        base_prompt = ""
        
        # 1. Definición del Tono Lingüístico (Perfil de Usuario)
        if user_profile == "engineer":
            base_prompt += "Eres un Ingeniero Ambiental y Jefe de Planta de Tratamiento. Hablas con rigor técnico, "
            base_prompt += "utilizas nomenclatura científica estricta (cinética de reactores, parámetros fisicoquímicos) "
            base_prompt += "y justificas tus decisiones con base en procesos biológicos y ecuaciones de estado.\n\n"
        else:
            base_prompt += "Eres un Supervisor Operativo de PTAR experimentado. Eres directo, claro y pragmático. "
            base_prompt += "Proporcionas instrucciones paso a paso, priorizas la seguridad industrial e integridad del equipo, "
            base_prompt += "y evitas jerga científica innecesaria. Tu objetivo es estabilizar el reactor rápidamente.\n\n"

        # 2. Definición de la Restricción de Conocimiento (Estrategia CBR vs RAG)
        if routing_strategy == "CBR":
            base_prompt += "RESTRICCIÓN CRÍTICA: La información que tienes a continuación proviene de la BITÁCORA EMPÍRICA "
            base_prompt += "de otros operarios de la planta. No es teoría estándar, es experiencia local probada.\n"
            base_prompt += "Basado EXCLUSIVAMENTE en estos casos empíricos resueltos, dile al usuario cómo solucionar el problema.\n"
            base_prompt += "Inicia tu respuesta aclarando explícitamente que esta directriz se basa en la experiencia histórica del personal de la planta.\n\n"
        else:
            base_prompt += "RESTRICCIÓN CRÍTICA: No existen registros empíricos locales para esta falla. La información a continuación "
            base_prompt += "proviene de los MANUALES DE OPERACIÓN TÉCNICA y la NORMATIVA AMBIENTAL VIGENTE.\n"
            base_prompt += "Basado EXCLUSIVAMENTE en la literatura recuperada, elabora una solución técnica para el problema.\n"
            base_prompt += "Si la solución no puede deducirse del texto provisto, indica que requieres inspección presencial y no alucines respuestas.\n\n"
            
        base_prompt += f"CONTEXTO RECUPERADO DE LA BASE DE DATOS VECTORIAL:\n{context}\n\n"
        base_prompt += "INSTRUCCIÓN FINAL: Responde únicamente a la pregunta del usuario utilizando el contexto anterior, respetando tu rol asignado."
        
        return base_prompt

    def generate_response(self, query: str, routing_strategy: str, documents: List[Dict[str, Any]], user_profile: str = "operator") -> Dict[str, Any]:
        """
        Genera una inferencia completa de una sola vez (síncrona).
        """
        context_str = self._build_context_string(documents)
        system_prompt = self._get_system_prompt(routing_strategy, user_profile, context_str)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "stream": False,
            "options": {
                # Reducimos la temperatura para el ingeniero (mayor precisión matemática) 
                # y la aumentamos levemente para el operario (mayor adaptabilidad lingüística).
                "temperature": 0.1 if user_profile == "engineer" else 0.3
            }
        }
        
        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            return {
                "answer": data.get("message", {}).get("content", ""),
                "primary_source_type": routing_strategy,
                "sources": documents
            }
        except Exception as e:
            logger.error(f"Error de red en la inferencia LLM con Ollama: {str(e)}")
            raise e

    def stream_response(self, query: str, routing_strategy: str, documents: List[Dict[str, Any]], user_profile: str = "operator") -> Generator[str, None, None]:
        """
        Generador asíncrono que consume el endpoint de Ollama manteniendo el socket TCP abierto.
        Lee los tokens a medida que se generan y los despacha al frontend, mitigando el TTFT (Time To First Token).
        """
        context_str = self._build_context_string(documents)
        system_prompt = self._get_system_prompt(routing_strategy, user_profile, context_str)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "stream": True,
            "options": {
                "temperature": 0.1 if user_profile == "engineer" else 0.3
            }
        }
        
        try:
            # La petición HTTP se hace con stream=True
            response = requests.post(self.api_endpoint, json=payload, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
        except Exception as e:
            logger.error(f"Interrupción en el streaming LLM: {str(e)}")
            yield f"\n[Fallo crítico de conexión con el motor cognitivo: {str(e)}]"

# Singleton global del servicio
rag_service = RAGEngine()