from typing import Protocol
from app.models import Message


class MessageRepositoryInterface(Protocol):
    async def create(self, request: any) -> Message: ...
