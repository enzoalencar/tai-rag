from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from typing import Optional
from sqlalchemy import UUID, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

class Agent(Base):
    __tablename__ = 'agents'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    config: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

class Context(Base):
    __tablename__ = 'contexts'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    initial_prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=False
    )
    context_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("contexts.id"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    
class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False
    )
    role: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    