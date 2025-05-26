from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserDTO(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    status: int
    created_at: datetime

    class Config:
        orm_mode = True