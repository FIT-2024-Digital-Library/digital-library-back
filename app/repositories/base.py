from abc import ABC, abstractmethod

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection


class SQLAlchemyRepository(ABC):
    @abstractmethod
    async def get(cls, connection: AsyncConnection, element_id: int):
        pass

    @abstractmethod
    async def get_multiple(cls, connection: AsyncConnection):
        pass

    @abstractmethod
    async def create(cls, connection: AsyncConnection, model: BaseModel):
        pass

    @abstractmethod
    async def delete(cls, connection: AsyncConnection, element_id: int):
        pass

    @abstractmethod
    async def update(cls, connection: AsyncConnection, element_id: int, model: BaseModel):
        pass
