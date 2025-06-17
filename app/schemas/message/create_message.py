from uuid import UUID
from pydantic import BaseModel


class CreateMessage(BaseModel):
    conversation_id: UUID
    role: int
    content: str