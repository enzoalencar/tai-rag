from app.models import Context
from typing import Protocol


class ContextRepositoryInterface(Protocol):
    async def get_by_title(self, title: str) -> Context | None: ...