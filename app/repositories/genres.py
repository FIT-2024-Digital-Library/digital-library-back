from typing import List, Optional
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.exc import IntegrityError

from app.models import Genre
from app.schemas import GenreCreate
from app.utils import CrudException

from .base import SQLAlchemyRepository


class GenresRepository(SQLAlchemyRepository):
    @classmethod
    async def get(cls, connection: AsyncConnection, genre_id: int) -> Optional[Genre]:
        result = await connection.execute(
            select(Genre)
            .where(Genre.id == genre_id)
        )
        return result.mappings().first()

    @classmethod
    async def get_multiple(
            cls,
            connection: AsyncConnection,
            name: Optional[str] = None
    ) -> List[Genre]:
        query = select(Genre)

        if name is not None:
            query = query.where(Genre.name.ilike(f"%{name}%"))

        result = await connection.execute(query)
        return result.mappings().all()

    @classmethod
    async def create(cls, connection: AsyncConnection, genre: GenreCreate) -> int:
        """Создать нового автора"""
        result = await connection.execute(
            insert(Genre)
            .values(name=genre.name)
            .returning(Genre.id)
        )
        return result.scalar_one()

    @classmethod
    async def get_existent_or_create(
            cls,
            connection: AsyncConnection,
            genre: GenreCreate
    ) -> int:
        existing_genres = await cls.get_multiple(connection, name=genre.name)

        if existing_genres:
            return existing_genres[0].id

        result = await connection.execute(
            insert(Genre)
            .values(name=genre.name)
            .returning(Genre.id)
        )
        return result.scalar_one()

    @classmethod
    async def delete(cls, connection: AsyncConnection, genre_id: int) -> Optional[Genre]:
        try:
            genre = await cls.get(connection, genre_id)
            if genre:
                await connection.execute(
                    delete(Genre)
                    .where(Genre.id == genre_id)
                )
            return genre
        except IntegrityError as e:
            raise CrudException(
                "Cannot delete genre - it is referenced by other records"
            )

    @classmethod
    async def update(
            cls,
            connection: AsyncConnection,
            genre_id: int,
            genre: GenreCreate
    ) -> Optional[Genre]:
        try:
            genre_in_db = await cls.get(connection, genre_id)
            if genre_in_db:
                await connection.execute(
                    update(Genre)
                    .where(Genre.id == genre_id)
                    .values(name=genre.name)
                )
            return genre_in_db
        except IntegrityError as e:
            raise CrudException(
                "Cannot update genre - integrity constraint violation"
            )
