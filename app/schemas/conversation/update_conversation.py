from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ConversationUpdate(BaseModel):
    user_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    context_id: Optional[UUID] = None
    title: Optional[str] = None
    status: Optional[int] = None