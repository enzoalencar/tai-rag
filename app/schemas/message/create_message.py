from uuid import UUID
from pydantic import BaseModel


class MessageBase(BaseModel):
    conversation_id: UUID
    role: int
    content: str