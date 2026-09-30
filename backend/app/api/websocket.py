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

PROFILES = {
    "operator": {
        "temperature": 0.3,
        "system": (
            "Eres el Asistente Operativo de la PTAR. Tu único propósito es brindar soluciones técnicas, directas y prácticas al personal de planta. "
            "REGLAS ESTRICTAS E INQUEBRANTABLES: "
            "1. Analiza el [HISTORIAL DE LA CONVERSACIÓN] para mantener la fluidez del diagnóstico. "
            "2. Si el [CONTEXTO PTAR] contiene información, enumera de inmediato las posibles causas y las acciones operativas a ejecutar. "
            "3. NUNCA utilices frases como 'Según la base de datos', 'En mis manuales', 'No tengo información' o 'El contexto dice'. Responde con naturalidad humana. "
            "4. Si la consulta es genérica o el contexto dice 'AMBIGUO_O_VACIO', asume un rol proactivo: propone de inmediato las causas operativas más probables basadas en los principios de tratamiento de aguas, y finaliza tu mensaje con MÁXIMO UNA (1) sola pregunta para ayudar a acotar la falla. "
            "5. PRIORIDAD ABSOLUTA: Siempre ofrece valor técnico y soluciones primero. Tienes estrictamente prohibido responder únicamente con preguntas."
        )
    },
    "engineer": {
        "temperature": 0.1,
        "system": (
            "Eres el Ingeniero Jefe Analítico de la PTAR. Tu rol es el diagnóstico fenomenológico profundo. "
            "REGLAS ESTRICTAS E INQUEBRANTABLES: "
            "1. Revisa el [HISTORIAL DE LA CONVERSACIÓN] para garantizar trazabilidad. "
            "2. Si el [CONTEXTO PTAR] contiene datos, explica la anomalía y dicta acciones correctivas usando rigor termodinámico y fisicoquímico. "
            "3. NUNCA declares que tu información proviene de un contexto, vector o base de datos. "
            "4. Si el escenario es difuso o el contexto dice 'AMBIGUO_O_VACIO', formula de inmediato una hipótesis de ingeniería enumerando los posibles fallos en los equipos y formula MÁXIMO UNA (1) solicitud de variables de estado (presión, caudal, DBO, turbidez, etc.) al final de tu diagnóstico. "
            "5. PRIORIDAD ABSOLUTA: Tienes prohibido devolver un mensaje que solo contenga preguntas. Entrega siempre un diagnóstico preliminar exhaustivo."
        )
    }
}

@router.websocket("/stream")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Túnel WebSocket TCP establecido con éxito.")
    
    # Memoria de sesión instanciada. Retendrá el contexto mientras el túnel TCP siga vivo.
    session_history = []

    try:
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
                with engine.connect() as db_connection:
                    # Inyección del ID en la selección CBR
                    cbr_query = text("""
                        SELECT id, author, symptoms, action_taken, result,
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
                        strategy = "Bitácora Histórica Operativa"
                        context_data = (
                            f"CASO HISTÓRICO EMPÍRICO:\n"
                            f"ID: {cbr_result.id}\n"
                            f"Autor: {cbr_result.author}\n"
                            f"Síntomas: {cbr_result.symptoms}\n"
                            f"Acción ejecutada: {cbr_result.action_taken}\n"
                            f"Resultado final: {cbr_result.result}"
                        )
                        sources_list.append({
                            "author": f"Caso ID: {cbr_result.id} - {cbr_result.author}",
                            "similarity": cbr_result.similarity
                        })
                    else:
                        # Inyección del ID en la selección de RAG
                        rag_query = text("""
                            SELECT id, content, metadata, 
                                   1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                            FROM document_chunks
                            WHERE 1 - (embedding <=> CAST(:vec AS vector)) >= :threshold_rag
                            ORDER BY similarity DESC
                            LIMIT 2
                        """)
                        rag_results = db_connection.execute(rag_query, {"vec": vector_str, "threshold_rag": threshold - 0.1}).fetchall()
                        
                        if rag_results:
                            strategy = "Manuales y Normativa Técnica"
                            fragments = [f"Extracto (Doc ID {row.id} - {row.metadata}):\n{row.content}" for row in rag_results]
                            context_data = "\n\n".join(fragments)
                            for row in rag_results:
                                sources_list.append({
                                    "author": f"Documento ID: {row.id} - {row.metadata}",
                                    "similarity": row.similarity
                                })
                        else:
                            strategy = "Análisis Teórico"
                            context_data = "AMBIGUO_O_VACIO"

                await websocket.send_text(json.dumps({
                    "type": "metadata",
                    "strategy": strategy,
                    "sources_used": sources_list
                }))

                # Formateo dinámico del historial de los últimos 6 turnos para proteger la ventana de contexto
                history_text = ""
                if session_history:
                    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in session_history[-6:]])
                else:
                    history_text = "Inicio de la conversación."

                from langchain_community.llms import Ollama
                from langchain.prompts import PromptTemplate

                profile = PROFILES.get(profile_key, PROFILES["operator"])
                llm = Ollama(
                    base_url="http://llm_engine:11434",
                    model="llama3",
                    temperature=profile["temperature"]
                )

                prompt_t = PromptTemplate(
                    input_variables=["system", "history", "context", "question"],
                    template="{system}\n\n[HISTORIAL DE LA CONVERSACIÓN]\n{history}\n\n[CONTEXTO PTAR]\n{context}\n\n[PREGUNTA DEL OPERARIO]\n{question}\n\nRespuesta Directa:"
                )

                prompt_formatted = prompt_t.format(
                    system=profile["system"],
                    history=history_text,
                    context=context_data,
                    question=user_message
                )

                full_response = ""
                for chunk in llm.stream(prompt_formatted):
                    full_response += chunk
                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "content": chunk
                    }))

                # Inserción en la memoria a corto plazo al finalizar el flujo de tokens
                session_history.append({"role": "OPERARIO", "content": user_message})
                session_history.append({"role": "ASISTENTE", "content": full_response})

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
        logger.info("Cliente desconectado.")
    except Exception as e:
        logger.error(f"Fallo en enrutamiento: {str(e)}")
        await websocket.close()