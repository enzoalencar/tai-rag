from datetime import datetime
from uuid import uuid4
from app.models import Conversation
from typing import Protocol


class ConversationRepositoryInterface(Protocol):
    async def create(self, id: uuid4, user_id: uuid4, agent_id: uuid4, context_id: uuid4, title: str, status: int, created_at: datetime, updated_at: datetime) -> Conversation: ...