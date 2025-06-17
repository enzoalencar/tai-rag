from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ContextDTO(BaseModel):
    id: UUID
    title: str
    description: str
    created_at: datetime

    class Config:
        orm_mode = True