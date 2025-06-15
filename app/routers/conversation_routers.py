from datetime import datetime
from uuid import uuid4
from app.utils.di_container import get_chat_service
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse


from app.services.db import get_redis, chat_exists
from app.assistants.assistant import RAGAssistant
from app.services import ChatService
from app.assistants import INITIAL_PROMPT
from app.utils.openai import transcribe_audio
from app.utils.websocket import ConnectionManager

class ChatIn(BaseModel):
    message: str = Field(default=INITIAL_PROMPT)

class NewChatIn(BaseModel):
    theme_title: str = Field(default='Coffee') # todo :: Ver se essa é a melhor forma de receber o tema do chat

router = APIRouter()
manager = ConnectionManager()

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

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") != "message" or "content" not in data:
                await websocket.send_json({"type": "error", "message": "Invalid message"})
                continue

            message = data["content"]

            async def send_func(payload):
                await websocket.send_json(payload)

            await assistant.run(message=message, send_func=send_func)

    except WebSocketDisconnect:
        print(f"Cliente {client_id} desconectado")
    finally:
        await rdb.aclose()

@router.websocket("/ws/{chat_id}/{client_id}")
async def websocket_duo_practice(websocket: WebSocket, client_id: int):
    await manager.connect(websocket=websocket, client_id=client_id)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(sender_id=client_id, message=data, role="other_user", type="message")
    except WebSocketDisconnect:
        await manager.disconnect(client_id=client_id)
        await manager.broadcast(sender_id=None, message=f"O usuário #{client_id} saiu do chat", role="backend", type="info")