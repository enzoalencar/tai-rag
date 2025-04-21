from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# ============================
# Schemas para User
# ============================

class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserRead(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


# ============================
# Schemas para Agent
# ============================

class AgentBase(BaseModel):
    name: str
    model: str
    config: str

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    config: Optional[str] = None

class AgentRead(AgentBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


# ============================
# Schemas para Context (ou Contexts)
# ============================

class ContextBase(BaseModel):
    title: str
    description: str
    initial_prompt: str

class ContextCreate(ContextBase):
    pass

class ContextUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    initial_prompt: Optional[str] = None

class ContextRead(ContextBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


# ============================
# Schemas para Conversation
# ============================

class ConversationBase(BaseModel):
    user_id: UUID
    agent_id: UUID
    context_id: UUID
    title: str
    status: Optional[int] = 0

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    user_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    context_id: Optional[UUID] = None
    title: Optional[str] = None
    status: Optional[int] = None

class ConversationRead(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ============================
# Schemas para Message
# ============================

class MessageBase(BaseModel):
    conversation_id: UUID
    role: int
    content: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    conversation_id: Optional[UUID] = None
    role: Optional[int] = None
    content: Optional[str] = None

class MessageRead(MessageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
