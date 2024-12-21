from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.crud.genres import get_genre_from_db, get_genres_from_db, create_genre_in_db, \
    delete_genre_from_db, update_genre_in_db
from app.schemas import Genre, GenreCreate
from app.schemas.users import PrivilegesEnum, User
from app.settings import async_session_maker
from app.utils import CrudException
from app.utils.auth import get_current_user, user_has_permissions

router = APIRouter(
    prefix='/genres',
    tags=['genres']
)


@router.get('/', response_model=List[Genre], summary='Returns genres')
async def get_genres(name: Optional[str] = Query(None, description="Find by genre name")):
    async with async_session_maker() as session:
        genres = await get_genres_from_db(session, name)
        if genres is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genres


@router.get('/{genre_id}', response_model=Genre, summary='Returns genre')
async def get_genre(genre_id: int):
    async with async_session_maker() as session:
        genre = await get_genre_from_db(session, genre_id)
        if genre is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genre


@router.post('/create', response_model=int, summary='Creates genres')
async def create_genre(genre: GenreCreate,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        key = await get_genres_from_db(session, name=genre.name)
        if len(key) == 0:
            key = await create_genre_in_db(session, genre)
        else:
            raise HTTPException(status_code=409, detail="Genre already exists")
        await session.commit()
        return key


@router.delete('/{genre_id}/delete', response_model=Genre, summary='Deletes genres')
async def delete_genre(genre_id: int,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        try:
            genre = await delete_genre_from_db(session, genre_id)
            if genre is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            await session.commit()
            return genre
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.put('/{genre_id}/update', response_model=Genre, summary='Updates genres')
async def update_genre(genre_id: int, genre: GenreCreate,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        try:
            genre = await update_genre_in_db(session, genre_id, genre)
            if genre is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            await session.commit()
            return genre
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))
