from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.crud.genres import get_genre_from_db, get_genres_from_db, create_genre_in_db, delete_genre_from_db, \
    update_genre_in_db
from app.schemas import Genre, GenreCreate
from app.users.dependencies import get_current_user, get_current_admin_user

router = APIRouter(
    prefix='/genres',
    tags=['genres']
)


@router.get('/', response_model=List[Genre], summary='Returns genres')
async def get_genres(
        id: Optional[int] = Query(None, description="Filter by genre id"),
        name: Optional[str] = Query(None, description="Find by genre name")):
    if id or name:
        genre = await get_genre_from_db(id=id, name=name)
        if genre is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        genres = [genre]
    else:
        genres = await get_genres_from_db()

    return genres


@router.post('/create', response_model=int, summary='Creates genres')
async def create_genre(genre: GenreCreate, user_data=Depends(get_current_user)):
    key = await get_genre_from_db(name=genre.name)
    if key is None:
        key = await create_genre_in_db(genre)
    else:
        raise HTTPException(status_code=409, detail="Genre already exists")
    return key


@router.delete('/delete', response_model=Genre, summary='Deletes genres')
async def delete_genre(id: int, user_data=Depends(get_current_user)):
    genre = await delete_genre_from_db(id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.put('/update/{id}', response_model=Genre, summary='Updates genres')
async def delete_genre(id: int, genre: GenreCreate, user_data=Depends(get_current_user)):
    genre = await update_genre_in_db(id, genre)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre