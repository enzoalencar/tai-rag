from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class CreateConversation(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: UUID
    context_id: UUID
    title: str
    status: Optional[int] = 0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]