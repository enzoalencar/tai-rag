import asyncio
from typing import Dict, Optional
from fastapi import WebSocket
from app.assistants.assistant import RAGAssistant
from app.services.chat import ChatService

class Room:
    def __init__(self, mode: str):
        self.connections: Dict[str, WebSocket] = {}
        self.current_turn: Optional[str] = None
        self.mode = mode
        self.started = False
        self.lock = asyncio.Lock()
        self.is_assistant_thinking = False

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        for user_id, ws in list(self.connections.items()):
            if user_id != exclude:
                try:
                    await ws.send_json(message)
                except:
                    pass

class LobbyManager:
    def __init__(self, rdb):
        self.rooms: Dict[str, Room] = {}
        self.rdb = rdb
        self.chat_service: Optional[ChatService] = None

    def set_chat_service(self, chat_service: ChatService):
            self.chat_service = chat_service

    def get_room(self, room_id: str, mode: Optional[str] = None) -> Room:
        if room_id not in self.rooms:
            if not mode:
                raise Exception("Modo da sala deve ser fornecido ao criar.")
            self.rooms[room_id] = Room(mode)
        return self.rooms[room_id]

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket, mode: str):
        room = self.get_room(room_id, mode)
        await websocket.accept()
        room.connections[user_id] = websocket

        if room.current_turn is None:
            room.current_turn = user_id

        await room.broadcast({
            "type": "join",
            "user": user_id,
            "participants": list(room.connections.keys()),
            "current_turn": room.current_turn
        })

        async with room.lock:
            num_users = len(room.connections)

            async def broadcast_send(payload: dict):
                await room.broadcast(payload)

            if room.mode == "solo":
                if not room.started:
                    await websocket.send_json({
                        "type": "ready_to_start",
                        "message": "Você está sozinho. A prática com a IA vai começar."
                    })
                    room.started = True
                    room.is_assistant_thinking = True
                    await room.broadcast({"type": "thinking", "value": True})
                    assistant = RAGAssistant(chat_id=room_id, rdb=self.rdb, chat_service=self.chat_service)
                    try:
                        await assistant.run(message="start", send_func=broadcast_send, store_user_message=False)
                    except Exception as e:
                        await websocket.send_json({"type": "error", "message": str(e)})
                    finally:
                        room.is_assistant_thinking = False
                        await room.broadcast({"type": "thinking", "value": False})
                        await room.broadcast({
                            "type": "turn",
                            "current_turn": user_id
                        })


            elif room.mode == "group":
                if num_users < 2:
                    await websocket.send_json({
                        "type": "waiting",
                        "message": "Esperando outro participante para começar."
                    })
                else:
                    if not room.started:
                        await room.broadcast({
                            "type": "ready_to_start",
                            "participants": list(room.connections.keys()),
                            "current_turn": room.current_turn
                        })
                        room.started = True
                        assistant = RAGAssistant(chat_id=room_id, rdb=self.rdb, chat_service=self.chat_service)
                        try:
                            await assistant.run(message="start", send_func=broadcast_send, store_user_message=False)
                        except Exception as e:
                            await room.broadcast({"type": "error", "message": str(e)})

    async def disconnect(self, room_id: str, user_id: str):
        room = self.get_room(room_id)
        if user_id in room.connections:
            del room.connections[user_id]
            await room.broadcast({
                "type": "leave",
                "user": user_id,
                "participants": list(room.connections.keys())
            })
            if room.current_turn == user_id:
                if room.connections:
                    room.current_turn = list(room.connections.keys())[0]
                    await room.broadcast({
                        "type": "turn",
                        "current_turn": room.current_turn
                    })
                else:
                    room.current_turn = None
        if not room.connections:
            del self.rooms[room_id]

    async def switch_turn(self, room_id: str):
        room = self.get_room(room_id)
        users = list(room.connections.keys())
        if not users:
            room.current_turn = None
            return
        if room.current_turn not in users:
            room.current_turn = users[0]
        else:
            idx = users.index(room.current_turn)
            room.current_turn = users[(idx + 1) % len(users)]
        await room.broadcast({
            "type": "turn",
            "current_turn": room.current_turn
        })

    async def handle_message(self, room_id: str, user_id: str, content: str):
        room = self.get_room(room_id)
        
        if room.mode == "group" and user_id != room.current_turn:
            return

        if room.is_assistant_thinking:
            return

        room.is_assistant_thinking = True
        await room.broadcast({"type": "thinking", "value": True})

        await room.broadcast({
            "type": "message",
            "role": "user",
            "sender": user_id,
            "message": content
        })

        async def broadcast_send(payload: dict):
            await room.broadcast(payload)

        assistant = RAGAssistant(chat_id=room_id, rdb=self.rdb, chat_service=self.chat_service)
        try:
            await assistant.run(
                message=content,
                send_func=broadcast_send
            )
        except Exception as e:
            await room.broadcast({"type": "error", "message": str(e)})
        finally:
            room.is_assistant_thinking = False
            await room.broadcast({"type": "thinking", "value": False})

        if room.mode == "group":
            await self.switch_turn(room_id)
