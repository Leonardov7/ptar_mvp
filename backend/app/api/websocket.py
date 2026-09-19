import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from app.core.config import engine

router = APIRouter()
logger = logging.getLogger(__name__)

_embedder_instance = None

def get_embedding(text_input: str) -> list:
    global _embedder_instance
    if _embedder_instance is None:
        logger.info("Importando librerías pesadas de Machine Learning en tiempo de ejecución...")
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Inicializando modelo de embeddings en memoria RAM...")
            _embedder_instance = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Fallo crítico al cargar SentenceTransformer: {str(e)}")
            return []
            
    return _embedder_instance.encode(text_input).tolist()

# Se reduce la temperatura a niveles deterministas para evitar que el LLM invente respuestas.
# Se impone una restricción absoluta para que el modelo actúe únicamente como decodificador del contexto.
PROFILES = {
    "operator": {
        "temperature": 0.1,
        "system": (
            "Eres el Asistente Operativo de la PTAR. Tu rol es guiar al personal de planta usando lenguaje claro y directo. "
            "REGLA ABSOLUTA DE RESTRICCIÓN RAG: Solo puedes responder basándote ESTRICTAMENTE en el [CONTEXTO PTAR] proporcionado. "
            "Si el contexto dice 'VACÍO' o no contiene la solución exacta al problema, DEBES responder textualmente: "
            "'No poseo información en la base de datos (ni en bitácora ni en manuales) para resolver este incidente. Requiere inspección humana.' "
            "Bajo ninguna circunstancia utilices tu conocimiento general o pre-entrenado para deducir una respuesta."
        )
    },
    "engineer": {
        "temperature": 0.0,
        "system": (
            "Eres el Ingeniero Jefe Analítico de la PTAR. Usas terminología técnica rigurosa. "
            "REGLA ABSOLUTA DE RESTRICCIÓN RAG: Solo puedes responder basándote ESTRICTAMENTE en el [CONTEXTO PTAR] proporcionado. "
            "Si el contexto dice 'VACÍO' o carece de los datos necesarios, DEBES responder textualmente: "
            "'No existen datos empíricos ni normativos indexados en el espacio vectorial para diagnosticar este escenario.' "
            "Tienes terminantemente prohibido utilizar conocimiento teórico externo o formular hipótesis fuera del contexto."
        )
    }
}

@router.websocket("/stream")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Túnel WebSocket TCP establecido con éxito.")

    try:
        with engine.connect() as db_connection:
            while True:
                raw_payload = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_payload)
                except json.JSONDecodeError:
                    continue

                user_message = data.get("message", "")
                profile_key = data.get("profile", "operator")
                threshold = float(data.get("threshold", 0.85))

                if not user_message:
                    continue

                query_vector = get_embedding(user_message)
                if not query_vector:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "El motor de vectorización falló al cargar."
                    }))
                    continue
                    
                vector_str = str(query_vector)

                try:
                    # BÚSQUEDA 1: Razonamiento Basado en Casos (CBR)
                    cbr_query = text("""
                        SELECT author, symptoms, action_taken, result,
                               1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                        FROM knowledge_vectors
                        WHERE 1 - (embedding <=> CAST(:vec AS vector)) >= :threshold
                          AND source_type = 'empirical_case'
                        ORDER BY similarity DESC
                        LIMIT 1
                    """)

                    cbr_result = db_connection.execute(cbr_query, {"vec": vector_str, "threshold": threshold}).fetchone()

                    strategy = ""
                    context_data = ""
                    sources_list = []

                    if cbr_result:
                        strategy = f"Bitácora Histórica Operativa"
                        context_data = (
                            f"CASO HISTÓRICO EMPÍRICO:\n"
                            f"Autor: {cbr_result.author}\n"
                            f"Síntomas: {cbr_result.symptoms}\n"
                            f"Acción ejecutada: {cbr_result.action_taken}\n"
                            f"Resultado final: {cbr_result.result}"
                        )
                        sources_list.append({
                            "author": cbr_result.author,
                            "similarity": cbr_result.similarity
                        })
                    else:
                        # BÚSQUEDA 2: Ingesta Normativa (RAG)
                        # Se aplica un umbral ligeramente más tolerante para la literatura, o el mismo del CBR.
                        rag_query = text("""
                            SELECT content, doc_metadata, 
                                   1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                            FROM document_chunks
                            WHERE 1 - (embedding <=> CAST(:vec AS vector)) >= :threshold_rag
                            ORDER BY similarity DESC
                            LIMIT 2
                        """)
                        rag_results = db_connection.execute(rag_query, {"vec": vector_str, "threshold_rag": threshold - 0.1}).fetchall()
                        
                        if rag_results:
                            strategy = "Manuales y Normativa Técnica"
                            fragments = [f"Extracto ({row.doc_metadata}):\n{row.content}" for row in rag_results]
                            context_data = "\n\n".join(fragments)
                            for row in rag_results:
                                sources_list.append({
                                    "author": row.doc_metadata,
                                    "similarity": row.similarity
                                })
                        else:
                            # CORRECCIÓN ARQUITECTÓNICA: Si no hay vectores, se instruye explícitamente el vacío.
                            strategy = "Sin Datos en el Sistema"
                            context_data = "VACÍO"

                    await websocket.send_text(json.dumps({
                        "type": "metadata",
                        "strategy": strategy,
                        "sources_used": sources_list
                    }))

                    from langchain_community.llms import Ollama
                    from langchain.prompts import PromptTemplate

                    profile = PROFILES.get(profile_key, PROFILES["operator"])
                    llm = Ollama(
                        base_url="http://llm_engine:11434",
                        model="llama3",
                        temperature=profile["temperature"]
                    )

                    prompt_t = PromptTemplate(
                        input_variables=["system", "context", "question"],
                        template="{system}\n\n[CONTEXTO PTAR]\n{context}\n\n[PREGUNTA]\n{question}\n\nRespuesta:"
                    )

                    prompt_formatted = prompt_t.format(
                        system=profile["system"],
                        context=context_data,
                        question=user_message
                    )

                    for chunk in llm.stream(prompt_formatted):
                        await websocket.send_text(json.dumps({
                            "type": "token",
                            "content": chunk
                        }))

                    await websocket.send_text(json.dumps({
                        "type": "end_of_stream",
                        "content": ""
                    }))

                except Exception as e:
                    logger.error(f"Fallo interno en la cadena lógica: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": f"Fallo lógico en base de datos: {str(e)}"
                    }))

    except WebSocketDisconnect:
        logger.info("Cliente desconectado de manera limpia.")
    except Exception as e:
        logger.error(f"Fallo en enrutamiento lógico global: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"Fallo interno en el orquestador: {str(e)}"
            }))
        except:
            pass
        await websocket.close()