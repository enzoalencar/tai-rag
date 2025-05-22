from app.interfaces.databases import PostgresProviderInterface
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

class PostgresProvider(PostgresProviderInterface):
    def __init__(self):
        self.engine = create_async_engine(
            settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')
        )
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session