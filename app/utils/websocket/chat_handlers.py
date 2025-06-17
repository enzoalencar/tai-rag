import logging

from app.assistants import RAGAssistant
from app.utils.websocket.types import MessageType

class BaseChatHandler:
    def __init__(self, room, room_id: str, room_manager, user_id: str, websocket):
        self.room = room
        self.room_id = room_id
        self.room_manager = room_manager
        self.user_id = user_id
        self.websocket = websocket

    async def on_connect(self):
        raise NotImplementedError

    async def on_message(self, content: str):
        raise NotImplementedError

class SoloChatHandler(BaseChatHandler):
    async def on_connect(self):
        try:
            await self.websocket.send_json({
                "type": MessageType.READY.value,
                "message": "Você está sozinho. A prática com a IA vai começar."
            })
            if hasattr(self.room, "set_started"):
                await self.room.set_started()
            else:
                self.room.started = True

            await self._run_assistant("start")
        except Exception as e:
            logging.exception("Erro em SoloChatHandler.on_connect")
            try:
                await self.websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass

    async def on_message(self, content: str):
        try:
            await self.room.broadcast({
                "type": MessageType.MESSAGE.value,
                "role": "user",
                "sender": self.user_id,
                "message": content
            })
            await self._run_assistant(content)
        except Exception as e:
            logging.exception("Erro em SoloChatHandler.on_message")
            try:
                await self.room.broadcast({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass

    async def _run_assistant(self, message: str):
        try:
            await self.room.broadcast({
                "type": MessageType.THINKING.value,
                "value": True
            })
        except Exception:
            logging.exception("Erro ao notificar thinking=True em SoloChatHandler")

        assistant = RAGAssistant(
            chat_id=self.room_id,
            rdb=self.room_manager.rdb,
            chat_service=self.room_manager.get_chat_service()
        )

        async def send_func(payload: dict):
            await self.room.broadcast(payload)

        try:
            await assistant.run(
                message=message,
                send_func=send_func,
                store_user_message=(message != "start")
            )
        except Exception:
            logging.exception("Erro em SoloChatHandler._run_assistant")
            raise
        finally:
            try:
                await self.room.broadcast({
                    "type": MessageType.THINKING.value,
                    "value": False
                })
            except Exception:
                logging.exception("Erro ao notificar thinking=False em SoloChatHandler")

class GroupChatHandler(BaseChatHandler):
    async def on_connect(self):
        try:
            if hasattr(self.room, "get_users"):
                users = await self.room.get_users()
            else:
                users = list(self.room.connections.keys())

            if len(users) < 2:
                await self.websocket.send_json({
                    "type": MessageType.WAITING.value,
                    "message": "Esperando outro participante para começar."
                })
            else:
                if not getattr(self.room, "started", False):
                    if hasattr(self.room, "set_started"):
                        await self.room.set_started()
                    else:
                        self.room.started = True

                    if hasattr(self.room, "get_users"):
                        users = await self.room.get_users()
                    else:
                        users = list(self.room.connections.keys())
                    await self.room.broadcast({
                        "type": MessageType.READY.value,
                        "participants": users,
                        "current_turn": self.room.current_turn
                    })
                    await self._run_assistant("start")
        except Exception as e:
            logging.exception("Erro em GroupChatHandler.on_connect")
            try:
                await self.websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass

    async def on_message(self, content: str):
        try:
            if self.user_id != self.room.current_turn:
                return

            await self.room.broadcast({
                "type": MessageType.MESSAGE.value,
                "role": "user",
                "sender": self.user_id,
                "message": content
            })


            await self._run_assistant(content)


            if hasattr(self.room, "advance_turn"):
                new_turn = await self.room.advance_turn()
            else:
                users = list(self.room.connections.keys())
                idx = users.index(self.room.current_turn) if self.room.current_turn in users else 0
                self.room.current_turn = users[(idx + 1) % len(users)] if users else None
                new_turn = self.room.current_turn

            if new_turn is not None:
                await self.room.broadcast({
                    "type": MessageType.TURN.value,
                    "current_turn": new_turn
                })
        except Exception as e:
            logging.exception("Erro em GroupChatHandler.on_message")
            try:
                await self.room.broadcast({
                    "type": MessageType.ERROR.value,
                    "message": str(e)
                })
            except Exception:
                pass

    async def _run_assistant(self, message: str):
        try:
            await self.room.broadcast({
                "type": MessageType.THINKING.value,
                "value": True
            })
        except Exception:
            logging.exception("Erro ao notificar thinking=True em GroupChatHandler")

        assistant = RAGAssistant(
            chat_id=self.room_id,
            rdb=self.room_manager.rdb,
            chat_service=self.room_manager.get_chat_service()
        )

        async def send_func(payload: dict):
            await self.room.broadcast(payload)

        try:
            await assistant.run(message=message, send_func=send_func)
        except Exception:
            logging.exception("Erro em GroupChatHandler._run_assistant")
            raise
        finally:
            try:
                await self.room.broadcast({
                    "type": MessageType.THINKING.value,
                    "value": False
                })
            except Exception:
                logging.exception("Erro ao notificar thinking=False em GroupChatHandler")


def get_chat_handler(room, room_id: str, manager, user_id: str, websocket):
    mode = getattr(room, "mode", None)
    
    if mode == "solo":
        return SoloChatHandler(room, room_id, manager, user_id, websocket)
    elif mode == "group":
        return GroupChatHandler(room, room_id, manager, user_id, websocket)
    else:
        raise ValueError(f"Modo de sala inválido: {mode}")