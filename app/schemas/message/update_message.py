from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UpdateMessage(BaseModel):
    id: UUID
    conversation_id: Optional[UUID] = None
    role: Optional[int] = None
    content: Optional[str] = None