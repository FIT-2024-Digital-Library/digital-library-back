from typing import List, Optional
from fastapi import APIRouter, Query, Depends

from app.schemas import Genre, GenreCreate, PrivilegesEnum, User
from app.services import GenreService
from app.utils import UnitOfWork, get_uow
from app.utils.auth import user_has_permissions


router = APIRouter(
    prefix='/genres',
    tags=['genres']
)


@router.get('/', response_model=List[Genre], summary='Returns genres')
async def get_genres(
        name: Optional[str] = Query(None, description="Find by genre name"),
        uow: UnitOfWork = Depends(get_uow)
):
    return await GenreService.get_genres(name, uow)


@router.get('/{genre_id}', response_model=Genre, summary='Returns genre')
async def get_genre(genre_id: int, uow: UnitOfWork = Depends(get_uow)):
    return await GenreService.get_genre(genre_id, uow)


@router.post('/create', response_model=int, summary='Creates genres')
async def create_genre(
        genre: GenreCreate,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await GenreService.create_genre(genre, uow)


@router.delete('/{genre_id}/delete', response_model=Genre, summary='Deletes genres')
async def delete_genre(
        genre_id: int,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await GenreService.delete_genre(genre_id, uow)


@router.put('/{genre_id}/update', response_model=Genre, summary='Updates genres')
async def update_genre(
        genre_id: int, genre: GenreCreate,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await GenreService.update_genre(genre_id, genre, uow)
