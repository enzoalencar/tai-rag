from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class MessageDTO(BaseModel):
    id: UUID
    conversation_id: UUID
    role: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True