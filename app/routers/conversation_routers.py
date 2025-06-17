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

@router.post('/chats/{chat_id}')
async def chat(chat_id: str, chat_in: ChatIn, chat_service: ChatService = Depends(get_chat_service)):
    rdb = get_redis()
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    
    assistant = RAGAssistant(
        chat_id=chat_id,
        rdb=rdb,
        chat_service=chat_service
    )
    sse_stream = assistant.run(message=chat_in.message)
    return EventSourceResponse(sse_stream, background=rdb.aclose)

@router.websocket("/ws/solo/{chat_id}/{client_id}")
async def websocket_solo_practice(websocket: WebSocket, chat_id: str, client_id: str, chat_service: ChatService = Depends(get_chat_service)):
    await websocket.accept()
    rdb = get_redis()

    if not await chat_exists(rdb=rdb, chat_id=chat_id):
        await websocket.close(code=1008)
        return

    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb, chat_service=chat_service)

    async def send_func(payload):
        await websocket.send_json(payload)

    await assistant.run(
        message=INITIAL_PROMPT,
        send_func=send_func,
        store_user_message=False
    )
    
    await websocket.send_json({"type": "turn", "message": client_id})
    
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") != "message" or "content" not in data:
                await websocket.send_json({"type": "error", "message": "Invalid message"})
                continue

            message = data["content"]

            await websocket.send_json({"type": "turn", "message": "assistant"})
            await assistant.run(message=message, send_func=send_func)
            await websocket.send_json({"type": "turn", "message": client_id})

    except WebSocketDisconnect:
        print(f"Cliente {client_id} desconectado")
    finally:
        await rdb.aclose()

@router.websocket("/ws/room/{chat_id}/{client_id}")
async def websocket_room(
    websocket: WebSocket,
    chat_id: str,
    client_id: str,
    mode: str = Query("group"),
    chat_service: ChatService = Depends(get_chat_service)
):
    rdb = get_redis()

    if not await chat_exists(rdb=rdb, chat_id=chat_id):
        await websocket.accept()
        await websocket.close(code=1008)
        return

    room_manager.set_chat_service(chat_service)
    room_manager.rdb = rdb

    await room_manager.connect(room_id=chat_id, user_id=client_id, websocket=websocket, mode=mode)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message" and "message" in data:
                await room_manager.handle_message(chat_id, client_id, data["message"])
    except WebSocketDisconnect:
        await room_manager.disconnect(chat_id, client_id)
    except Exception:
        await room_manager.disconnect(chat_id, client_id)