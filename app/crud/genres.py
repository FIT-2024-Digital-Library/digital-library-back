from sqlalchemy import select, insert, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import genre_table
from app.schemas import GenreCreate
from app.utils import CrudException


async def get_genre_from_db(session: AsyncSession, genre_id: int):
    query = select(genre_table).where(genre_table.c.id == genre_id)
    result = await session.execute(query)
    return result.mappings().first()


async def get_genres_from_db(session: AsyncSession, name: str = None):
    if name is not None:
        query = select(genre_table).where(genre_table.c.name.ilike(f"%{name}%"))
    else:
        query = select(genre_table)
    result = await session.execute(query)
    return result.mappings().all()


async def create_genre_in_db(session: AsyncSession, genre: GenreCreate):
    query = insert(genre_table).values(**genre.model_dump())
    result = await session.execute(query)
    genre_id = result.inserted_primary_key[0]
    return genre_id


async def get_existent_or_create_genre_in_db(session: AsyncSession, genre: GenreCreate):
    genres_in_db = await get_genres_from_db(session, name=genre.name)
    if genres_in_db is None or len(genres_in_db) == 0:
        query = insert(genre_table).values(**genre.model_dump())
        result = await session.execute(query)
        genre_id = result.inserted_primary_key[0]
    else:
        genre_id = genres_in_db[0]["id"]
    return genre_id


async def delete_genre_from_db(session: AsyncSession, genre_id: int):
    try:
        genre = await get_genre_from_db(session, genre_id)
        if genre is not None:
            query = delete(genre_table).where(genre_table.c.id == genre_id)
            await session.execute(query)
        return genre
    except IntegrityError as e:
        raise CrudException("Update or delete on table violates foreign key constraint")


async def update_genre_in_db(session: AsyncSession, genre_id: int, genre: GenreCreate):
    try:
        genre_in_db = await get_genre_from_db(session, genre_id)
        if genre_in_db is not None:
            query = update(genre_table).where(genre_table.c.id == genre_id).values(**genre.model_dump())
            await session.execute(query)
            genre_in_db = await get_genre_from_db(session, genre_id)
        return genre_in_db
    except IntegrityError as e:
        raise CrudException("Update or delete on table violates foreign key constraint")
