from app.models.shared.base_entity import BaseEntity
from datetime import datetime
from sqlalchemy import UUID, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class Agent(BaseEntity):
    __tablename__ = 'agents'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    config: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())