from uuid import uuid4
from time import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.services.db import get_redis, create_chat, chat_exists, get_postgres, create_chat_pg
from app.assistants.assistant import RAGAssistant

class ChatIn(BaseModel):
    message: str

async def get_rdb():
    rdb = get_redis()
    try:
        yield rdb
    finally:
        await rdb.aclose()

async def get_pg():
    pg = get_postgres()
    with pg() as session:
        try:
            yield session
        finally:
            session.close()

router = APIRouter()

@router.post('/chats')
async def create_new_chat(rdb = Depends(get_rdb), pg = Depends(get_pg)):
    chat_id = uuid4()
    created = int(time())
    await create_chat(rdb, str(chat_id), created)
    # await create_chat_pg(pg, chat_id, created)

    return {'id': chat_id}

@router.post('/chats/{chat_id}')
async def chat(chat_id: str, chat_in: ChatIn):
    rdb = get_redis()
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb)
    sse_stream = assistant.run(message=chat_in.message)
    return EventSourceResponse(sse_stream, background=rdb.aclose)