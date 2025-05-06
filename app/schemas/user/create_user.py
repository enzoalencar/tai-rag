from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CreateUser(BaseModel):
    id: Optional[UUID]
    name: str
    email: Optional[str] = None
    status: Optional[int] = 0