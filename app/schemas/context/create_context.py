from uuid import UUID
from pydantic import BaseModel, EmailStr


class CreateContext(BaseModel):
    title: str
    description: str
    initial_prompt: str