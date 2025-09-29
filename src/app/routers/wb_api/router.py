from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
import asyncio
import json
import logging

from kucoin.ws_client import KucoinWsClient
from core.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Хранилище активных WebSocket соединений
active_connections: List[WebSocket] = []

# Глобальный WebSocket клиент для KuCoin
ws_client: KucoinWsClient = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


async def kucoin_message_handler(message: Dict[str, Any]):
    """Обработчик сообщений от KuCoin WebSocket"""
    try:
        # Отправляем сообщение всем подключенным клиентам
        await manager.broadcast(json.dumps(message))
    except Exception as e:
        logger.error(f"Error handling KuCoin message: {e}")


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для подключения клиентов"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обрабатываем команды от клиента
            if message.get("type") == "subscribe":
                topic = message.get("topic")
                if topic:
                    await subscribe_to_topic(topic)
                    await manager.send_personal_message(
                        json.dumps({"type": "subscribed", "topic": topic}), 
                        websocket
                    )
            
            elif message.get("type") == "unsubscribe":
                topic = message.get("topic")
                if topic:
                    await unsubscribe_from_topic(topic)
                    await manager.send_personal_message(
                        json.dumps({"type": "unsubscribed", "topic": topic}), 
                        websocket
                    )
            
            elif message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), 
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def subscribe_to_topic(topic: str):
    """Подписаться на топик KuCoin"""
    global ws_client
    
    try:
        if not ws_client:
            # Создаем WebSocket клиент для KuCoin
            loop = asyncio.get_running_loop()
            ws_client = await KucoinWsClient.create(
                loop=loop,
                client=None,  # Для публичных данных клиент не нужен
                callback=kucoin_message_handler,
                private=False
            )
        
        await ws_client.subscribe(topic)
        logger.info(f"Subscribed to topic: {topic}")
        
    except Exception as e:
        logger.error(f"Error subscribing to topic {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def unsubscribe_from_topic(topic: str):
    """Отписаться от топика KuCoin"""
    global ws_client
    
    try:
        if ws_client and topic in ws_client.topics:
            await ws_client.unsubscribe(topic)
            logger.info(f"Unsubscribed from topic: {topic}")
        
    except Exception as e:
        logger.error(f"Error unsubscribing from topic {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def get_active_topics():
    """Получить список активных топиков"""
    global ws_client
    
    if ws_client:
        return {"topics": list(ws_client.topics)}
    else:
        return {"topics": []}


@router.post("/subscribe/{topic}")
async def subscribe_topic_endpoint(topic: str):
    """HTTP endpoint для подписки на топик"""
    try:
        await subscribe_to_topic(topic)
        return {"message": f"Subscribed to topic: {topic}"}
    except Exception as e:
        logger.error(f"Error subscribing to topic {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe/{topic}")
async def unsubscribe_topic_endpoint(topic: str):
    """HTTP endpoint для отписки от топика"""
    try:
        await unsubscribe_from_topic(topic)
        return {"message": f"Unsubscribed from topic: {topic}"}
    except Exception as e:
        logger.error(f"Error unsubscribing from topic {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_connections_info():
    """Получить информацию о подключениях"""
    return {
        "active_connections": len(manager.active_connections),
        "active_topics": list(ws_client.topics) if ws_client else []
    }
