from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Подключить WebSocket клиента."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        print(f"WebSocket connected: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket):
        """Отключить WebSocket клиента."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        print(f"WebSocket disconnected: {len(self.active_connections)} total")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Отправить сообщение конкретному клиенту."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Отправить сообщение всем подключенным клиентам."""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_fraud_alert(self, check_data: Dict[str, Any]):
        """Отправить алерт о подозрительной транзакции."""
        alert = {
            "type": "fraud_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": check_data
        }
        await self.broadcast(alert)
    
    async def broadcast_metrics_update(self, metrics: Dict[str, Any]):
        """Отправить обновление метрик."""
        update = {
            "type": "metrics_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": metrics
        }
        await self.broadcast(update)
    
    def get_connection_count(self) -> int:
        """Количество активных соединений."""
        return len(self.active_connections)

# Глобальный менеджер WebSocket
websocket_manager = WebSocketManager()
