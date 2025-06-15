from app.interfaces.repositories import MessageRepositoryInterface
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository(MessageRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_id, role, content, created_at, updated_at) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=created_at,
            updated_at=updated_at,
        )
        
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message