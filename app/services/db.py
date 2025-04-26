import json
from uuid import uuid4
import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import TextField, VectorField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.json.path import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.conversation import Conversation
from app.models.message import Message

VECTOR_IDX_NAME = 'idx:vector'
VECTOR_IDX_PREFIX = 'vector:'
CHAT_IDX_NAME = 'idx:chat'
CHAT_IDX_PREFIX = 'chat:'

async def setup_db(rdb):
    try:
        await rdb.ft(VECTOR_IDX_NAME).dropindex(delete_documents=True)
        print(f"Deleted vector index '{VECTOR_IDX_NAME}' and all associated documents")
    except Exception as e:
        pass
    finally:
        await create_vector_index(rdb)

    try:
        await rdb.ft(CHAT_IDX_NAME).info()
    except Exception:
        await create_chat_index(rdb)

def get_redis():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def get_postgres():
    engine = create_engine(settings.DATABASE_URL)
    return sessionmaker(bind=engine)

# VECTORS
async def create_vector_index(rdb):
    schema = (
        TextField('$.chunk_id', no_stem=True, as_name='chunk_id'),
        TextField('$.text', as_name='text'),
        TextField('$.doc_name', as_name='doc_name'),
        VectorField(
            '$.vector',
            'FLAT',
            {
                'TYPE': 'FLOAT32',
                'DIM': settings.EMBEDDING_DIMENSIONS,
                'DISTANCE_METRIC': 'COSINE'
            },
            as_name='vector'
        )
    )
    try:
        await rdb.ft(VECTOR_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[VECTOR_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Vector index '{VECTOR_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating vector index '{VECTOR_IDX_NAME}': {e}")

async def add_chunks_to_vector_db(rdb, chunks):
    async with rdb.pipeline(transaction=True) as pipe:
        for chunk in chunks:
            pipe.json().set(VECTOR_IDX_PREFIX + chunk['chunk_id'], Path.root_path(), chunk)
        await pipe.execute()

async def search_vector_db(rdb, query_vector, top_k=settings.VECTOR_SEARCH_TOP_K):
    query = (
        Query(f'(*)=>[KNN {top_k} @vector $query_vector AS score]')
        .sort_by('score')
        .return_fields('score', 'chunk_id', 'text', 'doc_name')
        .dialect(2)
    )
    res = await rdb.ft(VECTOR_IDX_NAME).search(query, {
        'query_vector': np.array(query_vector, dtype=np.float32).tobytes()
    })
    return [{
        'score': 1 - float(d.score),
        'chunk_id': d.chunk_id,
        'text': d.text,
        'doc_name': d.doc_name
    } for d in res.docs]

async def get_all_vectors(rdb):
    count = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, 0))
    res = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, count.total))
    return [json.loads(doc.json) for doc in res.docs]


# CHATS
async def create_chat_index(rdb):
    try:
        schema = (
            NumericField('$.created', as_name='created', sortable=True),
        )
        await rdb.ft(CHAT_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[CHAT_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Chat index '{CHAT_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating chat index '{CHAT_IDX_NAME}': {e}")

async def create_chat(rdb, chat_id, created):
    chat = {'id': chat_id, 'created': created, 'messages': []}
    await rdb.json().set(CHAT_IDX_PREFIX + chat_id, Path.root_path(), chat)
    return chat

async def create_chat_pg(pg, chat_id, created):
    model = Conversation(
        id=chat_id,
        user_id=uuid4(),
        agent_id=uuid4(),
        context_id=uuid4(),
        title='Coffee',
        status=0,
        created_at=created,
        updated_at=created,
    )

    pg.add(model)
    pg.commit()
    pg.refresh(model)
    print(f"Chat '{model.id}' created successfully")

async def add_chat_messages(rdb, chat_id, messages):
    await rdb.json().arrappend(CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)

async def add_chat_messages_pg(pg, messages):
    for message in messages:
        model = Message(
            conversation_id=uuid4(),
            role=message['role'],
            content=message['content'],
            created_at=message['created'],
            updated_at=message['created'],
        )

        pg.add(model)
        pg.commit()
        pg.refresh(model)
        print(f"Message from '{model.role}' successfully saved to DB")

async def chat_exists(rdb, chat_id):
    return await rdb.exists(CHAT_IDX_PREFIX + chat_id)

async def get_chat_messages(rdb, chat_id, last_n=None):
    if last_n is None:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, '$.messages[*]')
    else:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, f'$.messages[-{last_n}:]')
    return [{'role': m['role'], 'content': m['content']} for m in messages] if messages else []

async def get_chat(rdb, chat_id):
    return await rdb.json().get(chat_id)

async def get_all_chats(rdb):
    q = Query('*').sort_by('created', asc=False)
    count = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, 0))
    res = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, count.total))
    return [json.loads(doc.json) for doc in res.docs]
