from app.models import Context
from typing import Protocol


class ContextRepositoryInterface(Protocol):
    async def get_by_title(self, title: str) -> Context | None: ...

    async def get_by_id(self, id: str) -> Context | None: ...