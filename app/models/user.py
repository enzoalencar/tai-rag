from typing import Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base_entity import BaseEntity


class User(BaseEntity):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    status: Mapped[int] = mapped_column(default=0)
