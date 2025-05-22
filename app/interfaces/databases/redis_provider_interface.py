from abc import ABC, abstractmethod
from redis.asyncio import Redis


class RedisProviderInterface(ABC):
    @abstractmethod
    async def get_connection(self) -> Redis: ...