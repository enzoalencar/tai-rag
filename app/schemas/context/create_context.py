from uuid import UUID
from pydantic import BaseModel, EmailStr


class ContextCreate(BaseModel):
    title: str
    description: str
    initial_prompt: str