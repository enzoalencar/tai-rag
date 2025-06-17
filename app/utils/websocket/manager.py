import logging
from typing import Dict, Optional

from fastapi import WebSocket

from app.services.chat import ChatService
from app.utils.websocket.room import Room
from app.utils.websocket.chat_handlers import get_chat_handler
from app.utils.websocket.types import MessageType

class RoomManager:
    def __init__(self, rdb):
        self.rooms: Dict[str, Room] = {}
        self.rdb = rdb
        self.chat_service: Optional[ChatService] = None

    def set_chat_service(self, chat_service: ChatService):
        self.chat_service = chat_service

    def get_chat_service(self) -> ChatService:
        if not self.chat_service:
            raise RuntimeError("ChatService ainda não foi configurado.")
        return self.chat_service

    def get_or_create_room(self, room_id: str, mode: Optional[str] = None) -> Room:
        if room_id not in self.rooms:
            if not mode:
                raise ValueError("Modo da sala deve ser fornecido ao criar uma nova sala.")
            self.rooms[room_id] = Room(mode=mode)
            logging.info(f"[RoomManager] Sala criada: {room_id} (mode={mode})")
        return self.rooms[room_id]

    def get_room(self, room_id: str) -> Room:
        if room_id not in self.rooms:
            raise KeyError(f"Sala {room_id} não existe.")
        return self.rooms[room_id]

    def remove_room(self, room_id: str):
        if room_id in self.rooms:
            del self.rooms[room_id]
            logging.info(f"[RoomManager] Sala removida: {room_id}")

    def has_room(self, room_id: str) -> bool:
        return room_id in self.rooms

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket, mode: str):
        room = None
        try:
            room = self.get_or_create_room(room_id, mode)
            await room.add_user(user_id, websocket)
            if hasattr(room, "initialize_turn"):
                await room.initialize_turn(user_id)
            else:
                if room.current_turn is None:
                    room.current_turn = user_id

            handler = get_chat_handler(room, room_id, self, user_id, websocket)
            await handler.on_connect()

            users = await room.get_users() if hasattr(room, "get_users") else list(room.connections.keys())
            if room.mode == "group":
                await room.broadcast({
                    "type": MessageType.JOIN.value,
                    "user": user_id,
                    "participants": users,
                    "current_turn": room.current_turn
                })
        except Exception as e:
            logging.exception(f"[RoomManager] Erro ao conectar usuário {user_id} na sala {room_id}")
            try:
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass

    async def disconnect(self, room_id: str, user_id: str):
        try:
            room = self.get_room(room_id)
        except KeyError:
            return

        if hasattr(room, "remove_and_advance_turn"):
            new_turn = await room.remove_and_advance_turn(user_id)
        else:
            if user_id in room.connections:
                del room.connections[user_id]
            if room.current_turn == user_id:
                users = list(room.connections.keys())
                room.current_turn = users[0] if users else None
            new_turn = room.current_turn

        try:
            users = await room.get_users() if hasattr(room, "get_users") else list(room.connections.keys())
            await room.broadcast({
                "type": MessageType.LEAVE.value,
                "user": user_id,
                "participants": users
            })
        except Exception:
            logging.exception(f"[RoomManager] Erro ao notificar leave em sala {room_id}")

        if new_turn is not None:
            try:
                await room.broadcast({
                    "type": MessageType.TURN.value,
                    "current_turn": new_turn
                })
            except Exception:
                logging.exception(f"[RoomManager] Erro ao notificar novo turno em sala {room_id}")

        is_empty = await room.count_users() == 0 if hasattr(room, "count_users") else len(room.connections) == 0
        if is_empty:
            self.remove_room(room_id)

    async def handle_message(self, room_id: str, user_id: str, content: str):
        try:
            room = self.get_room(room_id)
        except KeyError:
            return

        websocket = room.connections.get(user_id)
        if not websocket:
            return

        handler = get_chat_handler(room, room_id, self, user_id, websocket)
        try:
            await handler.on_message(content)
        except Exception as e:
            logging.exception(f"[RoomManager] Erro em on_message para usuário {user_id} sala {room_id}")
            try:
                await room.broadcast({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass