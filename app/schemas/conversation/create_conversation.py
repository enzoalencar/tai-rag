from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CreateConversation(BaseModel):
    user_id: UUID
    agent_id: UUID
    context_id: UUID
    title: str
    status: Optional[int] = 0