from redis.commands.json.path import Path
from uuid import uuid4

from app.config import settings
from app.infra.agent_repository import AgentRepository
from app.infra.context_repository import ContextRepository
from app.schemas import CreateUser, CreateConversation, CreateMessage

class ChatService:
    def __init__(self, session):
        self.session = session

    async def create_chat_test(self, rdb, pg, chat_id, created, theme_title='Coffee'):
        # Redis
        chat = {'id': chat_id, 'created': created, 'messages': []}
        await rdb.json().set(settings.CHAT_IDX_PREFIX + chat_id, Path.root_path(), chat)

        # Postgres
        user = CreateUser(
            id=uuid4(),
            name='Temp',
            email=None,
        )

        agent = await AgentRepository.get_by_model(self.session, settings.MODEL)
        context = await ContextRepository.get_by_title(self.session, theme_title)

        conversation = CreateConversation(
            id=chat_id,
            user_id=user.id,
            agent_id=getattr(agent, 'id'),
            context_id=getattr(context, 'id'),
            title='Temp',
            status=0,
            created_at=created,
            updated_at=created,
        )

        pg.add(conversation)
        pg.commit()
        pg.refresh(conversation)
        return chat

    # async def create_messages_test(self, rdb, pg, chat_id, messages):
    #     await rdb.json().arrappend(settings.CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)
    #
    #     for message in messages:
    #         model = CreateMessage(
    #             conversation_id=uuid4(),
    #             role=message['role'],
    #             content=message['content'],
    #             created_at=message['created'],
    #             updated_at=message['created'],
    #         )
    #
    #         pg.add(model)
    #         pg.commit()
    #         pg.refresh(model)
    #         print(f"Message from '{model.role}' successfully saved to DB")