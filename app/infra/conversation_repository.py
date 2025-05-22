from datetime import datetime
from uuid import uuid4
from app.interfaces.repositories import ConversationRepositoryInterface
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation
from app.schemas import CreateConversation


class ConversationRepository(ConversationRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, id: uuid4, user_id: uuid4, agent_id: uuid4, context_id: uuid4, title: str, status: int, created_at: datetime, updated_at: datetime) -> Conversation:
        conversation = Conversation(
            id=id,
            user_id=user_id,
            agent_id=agent_id,
            context_id=context_id,
            title=title,
            status=status,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.session.add(conversation)
        await self.session.refresh(conversation)
        return conversation