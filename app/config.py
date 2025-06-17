from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MODEL: str = 'gpt-3.5-turbo-0125'
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    EMBEDDING_DIMENSIONS: int = 1024

    REDIS_HOST: Optional[str] = None 
    REDIS_PORT: Optional[int] = None 
    REDIS_URL: Optional[str] = None

    DOCS_DIR: str = 'datasets'

    PGHOST: Optional[str] = None
    PGPORT: Optional[int] = None
    PGUSER: Optional[str] = None
    PGPASSWORD: Optional[str] = None
    PGDATABASE: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    VECTOR_SEARCH_TOP_K: int = 10
    VECTOR_IDX_NAME: str = 'idx:vector'
    VECTOR_IDX_PREFIX: str = 'vector:'
    CHAT_IDX_NAME: str = 'idx:chat'
    CHAT_IDX_PREFIX: str = 'chat:'

    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)

    @property
    def resolved_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        host = self.PGHOST or 'localhost'
        port = self.PGPORT or 5432
        user = self.PGUSER or 'postgres'
        password = self.PGPASSWORD or ''
        db = self.PGDATABASE or 'tai_relational_db'
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    @property
    def resolved_redis_url(self) -> Optional[str]:
        if self.REDIS_URL:
            return self.REDIS_URL
        host = self.REDIS_HOST or 'localhost'
        port = self.REDIS_PORT or 6379
        return f"redis://{host}:{port}"

settings = Settings()