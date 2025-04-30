from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.crud_interface import CrudInterface
from app.models import Genre
from app.schemas import GenreCreate
from app.utils import CrudException


class GenresCrud(CrudInterface):
    @classmethod
    async def get(cls, session: AsyncSession, genre_id: int) -> Optional[Genre]:
        result = await session.execute(
            select(Genre)
            .where(Genre.id == genre_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_multiple(
            cls,
            session: AsyncSession,
            name: Optional[str] = None
    ) -> List[Genre]:
        query = select(Genre)

        if name is not None:
            query = query.where(Genre.name.ilike(f"%{name}%"))

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, genre: GenreCreate) -> int:
        new_genre = Genre(name=genre.name)
        session.add(new_genre)
        await session.flush()
        return new_genre.id

    @classmethod
    async def get_existent_or_create(
            cls,
            session: AsyncSession,
            genre: GenreCreate
    ) -> int:
        existing_genres = await cls.get_multiple(session, name=genre.name)

        if existing_genres:
            return existing_genres[0].id

        new_genre = Genre(name=genre.name)
        session.add(new_genre)
        await session.flush()
        return new_genre.id

    @classmethod
    async def delete(cls, session: AsyncSession, genre_id: int) -> Optional[Genre]:
        try:
            genre = await cls.get(session, genre_id)
            if genre:
                await session.delete(genre)
                await session.flush()
            return genre
        except IntegrityError as e:
            await session.rollback()
            raise CrudException(
                "Cannot delete genre - it is referenced by other records"
            )

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            genre_id: int,
            genre: GenreCreate
    ) -> Optional[Genre]:
        try:
            genre_in_db = await cls.get(session, genre_id)
            if genre_in_db:
                genre_in_db.name = genre.name
                await session.flush()
                await session.refresh(genre_in_db)
            return genre_in_db
        except IntegrityError as e:
            await session.rollback()
            raise CrudException(
                "Cannot update genre - integrity constraint violation"
            )
