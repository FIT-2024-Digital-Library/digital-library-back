from contextlib import asynccontextmanager
from contextvars import ContextVar
from fastapi import Depends
from typing import Annotated, Type, TypeVar

__all__ = ["UnitOfWork"]

from sqlalchemy.ext.asyncio import AsyncConnection

from app.settings import db_engine


class UnitOfWork:
    __connection = ContextVar("connection", default=None)

    @asynccontextmanager
    async def begin(self):
        async with db_engine.begin() as conn:
            token = self.__connection.set(conn)
            try:
                yield self
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
            finally:
                self.__connection.reset(token)

    def get_connection(self) -> AsyncConnection:
        current_connection = self.__connection.get()
        if current_connection is None:
            raise RuntimeError("Connection is not established. Use 'async with uow.begin()'.")
        return current_connection


def get_uow() -> UnitOfWork:
    return UnitOfWork()
