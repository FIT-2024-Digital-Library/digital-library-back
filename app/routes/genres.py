from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.crud.genres import GenresCrud
from app.schemas import Genre, GenreCreate, PrivilegesEnum, User
from app.utils import CrudException
from app.utils.auth import user_has_permissions
from app.utils.unit_of_work import UnitOfWork, get_uow


router = APIRouter(
    prefix='/genres',
    tags=['genres']
)


@router.get('/', response_model=List[Genre], summary='Returns genres')
async def get_genres(name: Optional[str] = Query(None, description="Find by genre name"),
                     uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        genres = await GenresCrud.get_multiple(uow.get_connection(), name)
        if genres is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genres


@router.get('/{genre_id}', response_model=Genre, summary='Returns genre')
async def get_genre(genre_id: int, uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        genre = await GenresCrud.get(uow.get_connection(), genre_id)
        if genre is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genre


@router.post('/create', response_model=int, summary='Creates genres')
async def create_genre(genre: GenreCreate,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                       uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        key = await GenresCrud.get_multiple(uow.get_connection(), name=genre.name)
        if len(key) == 0:
            key = await GenresCrud.create(uow.get_connection(), genre)
        else:
            raise HTTPException(status_code=409, detail="Genre already exists")
        # Commit is handled automatically by the UnitOfWork context manager.
        return key


@router.delete('/{genre_id}/delete', response_model=Genre, summary='Deletes genres')
async def delete_genre(genre_id: int,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                       uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        try:
            genre = await GenresCrud.delete(uow.get_connection(), genre_id)
            if genre is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            await uow.get_connection().commit()
            return genre
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.put('/{genre_id}/update', response_model=Genre, summary='Updates genres')
async def update_genre(genre_id: int, genre: GenreCreate,
                       user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                       uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        try:
            genre = await GenresCrud.update(uow.get_connection(), genre_id, genre)
            if genre is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            await uow.get_connection().commit()
            return genre
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))
