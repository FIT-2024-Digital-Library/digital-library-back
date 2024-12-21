from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

__all__ = ["db_engine", "async_session_maker"]


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='POSTGRES_', env_file="./config/postgres.env")
    user: str
    password: str
    hostname: str
    port: int
    db: str

    @property
    def postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.hostname}:{self.port}/{self.db}"


pg_cred = PostgresSettings()
db_engine = create_async_engine(pg_cred.postgres_url)
async_session_maker = async_sessionmaker(db_engine, expire_on_commit=False)
