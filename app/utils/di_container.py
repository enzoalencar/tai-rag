from fastapi import Depends
from app.infra.db.redis_provider import RedisProvider, PostgresProvider
from app.infra import UserRepository, AgentRepository, ContextRepository, ConversationRepository, MessageRepository
from app.services.chat import ChatService

# Providers de banco de dados
redis_provider = RedisProvider()
postgres_provider = PostgresProvider()

async def get_redis():
    redis = await redis_provider.get_connection()
    try:
        yield redis
    finally:
        await redis.aclose()

async def get_postgres():
    async for session in postgres_provider.get_session():
        yield session

# Repositories
async def get_user_repo(session=Depends(get_postgres)):
    return UserRepository(session)

async def get_agent_repo(session=Depends(get_postgres)):
    return AgentRepository(session)

async def get_context_repo(session=Depends(get_postgres)):
    return ContextRepository(session)

async def get_conversation_repo(session=Depends(get_postgres)):
    return ConversationRepository(session)

async def get_message_repo(session=Depends(get_postgres)):
    return MessageRepository(session)

# Services
async def get_chat_service(
    redis=Depends(get_redis),
    user_repo=Depends(get_user_repo),
    agent_repo=Depends(get_agent_repo),
    context_repo=Depends(get_context_repo),
    conversation_repo=Depends(get_conversation_repo),
    message_repo=Depends(get_message_repo)
):
    return ChatService(redis, user_repo, agent_repo, context_repo, conversation_repo, message_repo)