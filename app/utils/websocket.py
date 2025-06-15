from typing import Dict, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.current_turn: str = None

    async def notify_participants(self, exclude_id: Optional[str] = None):
        message = {
            "type": "participants",
            "count": len(self.active_connections)
        }
        
        for client_id, connection in self.active_connections.items():
            if client_id != exclude_id:
                await connection.send_json(message)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if self.current_turn is None:
            self.current_turn = client_id
        join_message = { "type": "join", "user": client_id }
        for cid, connection in self.active_connections.items():
            if cid != client_id:
                await self.safe_send(connection, join_message)
    
        await self.notify_participants(exclude_id=client_id)
        await self.send_turn_info()

    async def send_turn_info(self):
        message = {
            "type": "turn",
            "current_turn": self.current_turn
        }
        for connection in self.active_connections.values():
            await self.safe_send(connection, message)
            
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            was_current_turn = client_id == self.current_turn
            leave_message = { "type": "leave", "user": client_id }
            for cid, connection in self.active_connections.items():
                if cid != client_id:
                    await self.safe_send(connection, leave_message)
                
            del self.active_connections[client_id]

            if not self.active_connections:
                self.current_turn = None
                return

            if was_current_turn:
                await self.switch_turn()

            await self.notify_participants()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, sender_id: str, message: str, role: str, type: str):
        if sender_id != self.current_turn:
            return

        # TODO:  user name instead of sender_id
        
        message = {
            "type": type,
            "role": role,
            "message": message,
            "sender": sender_id 
        }
        
        for client_id, connection in self.active_connections.items():
            if client_id != sender_id:
                await self.safe_send(connection=connection, message=message)
        
        await self.switch_turn()

    async def switch_turn(self):
        if not self.active_connections:
            self.current_turn = None
            return
        
        clients = list(self.active_connections.keys())

        if self.current_turn not in clients:
            self.current_turn = clients[0]
        else:
            current_index = clients.index(self.current_turn)
            next_index = (current_index + 1) % len(clients)
            self.current_turn = clients[next_index]
        
        await self.send_turn_info()

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await self.safe_send(websocket, message)
        
    async def safe_send(self, connection: WebSocket, message: dict) -> None:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"[Erro ao enviar mensagem]: {e}")