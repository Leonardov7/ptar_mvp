import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.config import get_db
from app.services.cbr_router import cbr_service
from app.services.rag_engine import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/stream")
async def websocket_chat_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Túnel TCP bidireccional. Recibe peticiones JSON del cliente Vue.js y 
    transmite cadenas de texto (tokens) en tiempo real, junto con las fuentes.
    """
    await websocket.accept()
    logger.info("Conexión WebSocket establecida con el cliente Frontend.")
    
    try:
        while True:
            # 1. Esperar mensaje del usuario
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            query = payload.get("query", "")
            user_profile = payload.get("user_profile", "operator")
            similarity_threshold = payload.get("similarity_threshold", 0.85)
            
            if not query:
                await websocket.send_json({"error": "La consulta no puede estar vacía."})
                continue

            # 2. Ejecutar lógica de enrutamiento y recuperación (Bloqueante breve)
            routing_data = cbr_service.route_and_search(
                db=db, 
                query=query, 
                similarity_threshold=similarity_threshold
            )
            
            # Enviar notificación inicial al frontend indicando qué estrategia ganó
            await websocket.send_json({
                "type": "metadata",
                "routing_strategy": routing_data["routing_strategy"],
                "sources_used": routing_data["documents"]
            })
            
            # 3. Transmisión del streaming (Token a Token)
            generator = rag_service.stream_response(
                query=query,
                routing_strategy=routing_data["routing_strategy"],
                documents=routing_data["documents"],
                user_profile=user_profile
            )
            
            for token in generator:
                # Transmitir el fragmento de texto al cliente instantáneamente
                await websocket.send_json({
                    "type": "token",
                    "content": token
                })
                
            # Señal de finalización del mensaje actual
            await websocket.send_json({"type": "end_of_stream"})
            
    except WebSocketDisconnect:
        logger.info("El cliente Frontend cerró la conexión WebSocket.")
    except Exception as e:
        logger.error(f"Fallo no controlado en el canal WebSocket: {str(e)}")
        try:
            await websocket.send_json({"error": f"Fallo interno del servidor: {str(e)}"})
        except:
            pass