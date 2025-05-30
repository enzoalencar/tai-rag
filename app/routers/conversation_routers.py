from datetime import datetime
from uuid import uuid4
from app.utils.di_container import get_chat_service
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.services.db import get_redis, chat_exists
from app.assistants.assistant import RAGAssistant
from app.services import ChatService
from app.assistants import INITIAL_PROMPT


class ChatIn(BaseModel):
    message: str = Field(default=INITIAL_PROMPT)

class NewChatIn(BaseModel):
    theme_title: str = Field(default='Coffee') # todo :: Ver se essa é a melhor forma de receber o tema do chat

router = APIRouter()

@router.post('/chats')
async def new_chat(chat_in: NewChatIn, chat_service: ChatService = Depends(get_chat_service)):
    # todo :: Receber theme_title pelo body do post
    chat = await chat_service.create_chat(chat_in.theme_title)
    # todo :: Validar se precisa mesmo retornar objeto
    return {'id': chat['id']}

@router.post('/chats/{chat_id}')
async def chat(chat_id: str, chat_in: ChatIn):
    rdb = get_redis()
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb)
    sse_stream = assistant.run(message=chat_in.message)
    return EventSourceResponse(sse_stream, background=rdb.aclose)