from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    ALLOW_ORIGINS: str = '*'
    OPENAI_API_KEY: str
    MODEL: str = 'gpt-3.5-turbo-0125'
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    EMBEDDING_DIMENSIONS: int = 1024
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    DOCS_DIR: str = 'datasets'
    EXPORT_DIR: str = 'data'
    VECTOR_SEARCH_TOP_K: int = 10

    DB_HOST: str = 'postgres'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DATABASE_NAME: str = 'tai_relational_db'

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DATABASE_NAME}"

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()