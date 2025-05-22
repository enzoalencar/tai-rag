from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresProviderInterface(ABC):
    @abstractmethod
    async def get_session(self) -> AsyncSession: ...