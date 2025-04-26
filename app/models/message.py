from app.models.shared.base_entity import BaseEntity
from datetime import datetime
from sqlalchemy import UUID, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class Message(BaseEntity):
    __tablename__ = 'messages'

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())