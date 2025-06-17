from app.interfaces.databases import RedisProviderInterface
from redis.asyncio import Redis
from app.config import settings

class RedisProvider(RedisProviderInterface):
    async def get_connection(self) -> Redis:
        return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)