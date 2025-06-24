from app.settings import db_engine
from app.models import db_metadata


__all__ = ["create_tables", "close_connections", "delete_tables"]


async def create_tables() -> None:
    async with db_engine.begin() as connection:
        await connection.run_sync(db_metadata.create_all)


async def close_connections():
    await db_engine.dispose()


## shell: python -c "import asyncio; from app.utils import delete_tables; asyncio.run(delete_tables())"
async def delete_tables() -> None:
    async with db_engine.begin() as connection:
        await connection.run_sync(db_metadata.drop_all)
