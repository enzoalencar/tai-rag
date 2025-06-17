from typing import Optional
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared import BaseEntity


class Agent(BaseEntity):
    __tablename__ = 'agents'

    name: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    config: Mapped[Optional[str]] = mapped_column(Text)
