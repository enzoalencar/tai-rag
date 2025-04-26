from app.models.shared.base_entity import BaseEntity
from datetime import datetime
from sqlalchemy import UUID, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class Conversation(BaseEntity):
    __tablename__ = 'conversations'

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    context_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contexts.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())