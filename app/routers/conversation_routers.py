from datetime import datetime
from uuid import uuid4
from app.utils.di_container import get_chat_service
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse


from app.services.db import get_redis, chat_exists
from app.assistants.assistant import RAGAssistant
from app.services import ChatService
from app.assistants import INITIAL_PROMPT
from app.utils.openai import transcribe_audio
from app.utils.websocket import RoomManager


class ChatIn(BaseModel):
    message: str = Field(default=INITIAL_PROMPT)

class NewChatIn(BaseModel):
    theme_title: str = Field(default='Coffee') # todo :: Ver se essa é a melhor forma de receber o tema do chat

router = APIRouter()
room_manager = RoomManager(rdb=get_redis())

@router.post('/chats')
async def new_chat(chat_in: NewChatIn, chat_service: ChatService = Depends(get_chat_service)):
    # todo :: Receber theme_title pelo body do post
    chat = await chat_service.create_chat(chat_in.theme_title)
    # todo :: Validar se precisa mesmo retornar objeto
    return {'id': chat['id']}

@router.websocket("/ws/solo/{chat_id}/{client_id}")
async def websocket_solo_practice(websocket: WebSocket, chat_id: str, client_id: str, chat_service: ChatService = Depends(get_chat_service)):
    rdb = get_redis()

    if not await chat_exists(rdb=rdb, chat_id=chat_id):
        await websocket.accept()
        await websocket.close(code=1008)
        return

    room_manager.set_chat_service(chat_service)
    room_manager.rdb = rdb

    await room_manager.connect(room_id=chat_id, user_id=client_id, websocket=websocket, mode="solo")

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message" and "message" in data:
                await room_manager.handle_message(chat_id, client_id, data["message"])
    except WebSocketDisconnect:
        await room_manager.disconnect(chat_id, client_id)
    except Exception:
        await room_manager.disconnect(chat_id, client_id)

@router.websocket("/ws/group/{chat_id}/{client_id}")
async def websocket_group_practice(
    websocket: WebSocket,
    chat_id: str,
    client_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    rdb = get_redis()

    if not await chat_exists(rdb=rdb, chat_id=chat_id):
        await websocket.accept()
        await websocket.close(code=1008)
        return

    room_manager.set_chat_service(chat_service)
    room_manager.rdb = rdb

    await room_manager.connect(room_id=chat_id, user_id=client_id, websocket=websocket, mode="group")

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message" and "message" in data:
                await room_manager.handle_message(chat_id, client_id, data["message"])
    except WebSocketDisconnect:
        await room_manager.disconnect(chat_id, client_id)
    except Exception:
        await room_manager.disconnect(chat_id, client_id)