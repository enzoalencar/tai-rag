from datetime import datetime
from uuid import uuid4
from app.interfaces import UserRepositoryInterface, AgentRepositoryInterface, ContextRepositoryInterface, ConversationRepositoryInterface, MessageRepositoryInterface
from redis.commands.json.path import Path
from redis.asyncio import Redis

from app.config import settings


class ChatService:
    def __init__(self, rdb: Redis, user_repo: UserRepositoryInterface, agent_repo: AgentRepositoryInterface, context_repo: ContextRepositoryInterface, conversation_repo: ConversationRepositoryInterface, message_repo: MessageRepositoryInterface):
        self.rdb = rdb
        self.user_repo = user_repo
        self.agent_repo = agent_repo
        self.context_repo = context_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    # async def create_chat(self, chat_id, created, theme_title='Coffee') -> dict:
    async def create_chat(self, theme_title='Coffee') -> dict:
        chat_id = uuid4()
        created = datetime.now()

        chat = {'id': str(chat_id), 'created': created, 'messages': []}
        await self.rdb.json().set(settings.CHAT_IDX_PREFIX + str(chat_id), Path.root_path(), chat)

        user = await self.user_repo.create_temp()
        agent = await self.agent_repo.get_by_model(settings.MODEL)
        context = await self.context_repo.get_by_title(theme_title)

        await self.conversation_repo.create(
            id=chat_id,
            user_id=user.id,
            agent_id=getattr(agent, 'id'),
            context_id=getattr(context, 'id'),
            title=theme_title,
            status=0,
            created_at=created,
            updated_at=created,
        )

        return chat

    async def add_chat_messages(self, chat_id, messages):
        await self.rdb.json().arrappend(settings.CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)
    
        for message in messages:
            await self.message_repo.create(
                conversation_id=chat_id,
                role=message['role'],
                content=message['content'],
                created_at=message['created'],
                updated_at=message['created'],
            )