from typing import Protocol
from app.models import Message


class MessageRepositoryInterface(Protocol):
    async def create(self, conversation_id, role, content, created_at, updated_at) -> Message: ...
