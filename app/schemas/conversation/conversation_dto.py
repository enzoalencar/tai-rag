from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ConversationDTO(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: UUID
    context_id: UUID
    title: str
    status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True