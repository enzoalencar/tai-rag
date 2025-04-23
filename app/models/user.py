from app.models.shared.base_entity import BaseEntity
from datetime import datetime
from typing import Optional
from sqlalchemy import UUID, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid


class User(BaseEntity):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    status: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())