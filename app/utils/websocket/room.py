import asyncio
import logging
from typing import Dict, Optional, List

from fastapi import WebSocket

class Room:
    def __init__(self, mode: str):
        self.mode = mode
        self.connections: Dict[str, WebSocket] = {}
        self.current_turn: Optional[str] = None
        self.started: bool = False
        self.is_assistant_thinking: bool = False
        self.lock = asyncio.Lock()

    async def add_user(self, user_id: str, websocket: WebSocket):
        async with self.lock:
            await websocket.accept()
            self.connections[user_id] = websocket
            logging.info(f"[Room] Usuário {user_id} adicionado na sala (mode={self.mode}).")

    async def remove_user(self, user_id: str):
        async with self.lock:
            if user_id in self.connections:
                del self.connections[user_id]
                logging.info(f"[Room] Usuário {user_id} removido da sala.")
            else:
                logging.debug(f"[Room] Tentou remover usuário {user_id}, mas não estava presente.")

    async def get_users(self) -> List[str]:
        async with self.lock:
            return list(self.connections.keys())

    def is_empty(self) -> bool:
        return len(self.connections) == 0

    async def initialize_turn(self, user_id: str):
        async with self.lock:
            if self.current_turn is None:
                self.current_turn = user_id
                logging.info(f"[Room] Turno inicial definido para usuário {user_id}.")

    async def remove_and_advance_turn(self, user_id: str) -> Optional[str]:
        async with self.lock:
            existed = self.connections.pop(user_id, None) is not None
            if existed:
                logging.info(f"[Room] remove_and_advance_turn: usuário {user_id} removido.")
            if self.current_turn == user_id:
                users = list(self.connections.keys())
                if users:
                    self.current_turn = users[0]
                    logging.info(f"[Room] Turno avançado para {self.current_turn} após remoção de {user_id}.")
                else:
                    self.current_turn = None
                    logging.info(f"[Room] Sala vazia após remoção de {user_id}; current_turn=None.")
            return self.current_turn

    async def advance_turn(self) -> Optional[str]:
        async with self.lock:
            users = list(self.connections.keys())
            if not users:
                self.current_turn = None
                logging.info("[Room] advance_turn: sala vazia, current_turn=None.")
                return None

            if self.current_turn not in users:
                self.current_turn = users[0]
                logging.info(f"[Room] advance_turn: current_turn não existia, definido para {self.current_turn}.")
            else:
                idx = users.index(self.current_turn)
                self.current_turn = users[(idx + 1) % len(users)]
                logging.info(f"[Room] advance_turn: turno avançado para {self.current_turn}.")
            return self.current_turn

    async def set_started(self):
        async with self.lock:
            if not self.started:
                self.started = True
                logging.info(f"[Room] Sala iniciada (mode={self.mode}).")

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        async with self.lock:
            conns = list(self.connections.items())
        for uid, ws in conns:
            if uid == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception as e:
                logging.error(f"[Room.broadcast] falha ao enviar para {uid}: {e}")
             
    async def count_users(self) -> int:
        async with self.lock:
            return len(self.connections)