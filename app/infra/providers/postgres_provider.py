from app.interfaces.databases import PostgresProviderInterface
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

def adapt_db_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        return url
    elif url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    else:
        raise ValueError(f"URL de banco de dados inválida: {url}")

class PostgresProvider(PostgresProviderInterface):
    def __init__(self):
        db_url = adapt_db_url(settings.DATABASE_URL)
        self.engine = create_async_engine(db_url)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session