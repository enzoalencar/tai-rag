from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DeleteConversation(BaseModel):
    id: UUID
    status: int