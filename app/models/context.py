from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.shared.base_entity import BaseEntity


class Context(BaseEntity):
    __tablename__ = 'contexts'

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    initial_prompt: Mapped[str] = mapped_column(Text)
