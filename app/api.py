from uuid import uuid4
from time import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.db import get_redis, create_chat, chat_exists
from app.assistants.assistant import RAGAssistant
from fastapi.responses import StreamingResponse

class ChatIn(BaseModel):
    message: str

async def get_rdb():
    rdb = get_redis()
    try:
        yield rdb
    finally:
        await rdb.aclose()

router = APIRouter()

@router.post('/chats')
async def create_new_chat(rdb = Depends(get_rdb)):
    chat_id = str(uuid4())[:8]
    created = int(time())
    await create_chat(rdb, chat_id, created)
    return {'id': chat_id}

@router.post('/chats/{chat_id}')
async def chat(chat_id: str, chat_in: ChatIn):
    rdb = get_redis()
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb)
    sse_stream = assistant.run(message=chat_in.message)
    return EventSourceResponse(sse_stream, background=rdb.aclose)

@router.get('/sse_response')
async def sse_response(chat_id: str, chat_in: ChatIn):
    rdb = get_redis()
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb)
    sse_stream = assistant.run(message=chat_in.message)
    return StreamingResponse(sse_stream, background=rdb.aclose)