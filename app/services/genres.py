from typing import List, Optional
from fastapi import HTTPException

from app.repositories import GenresRepository
from app.schemas import Genre, GenreCreate, PrivilegesEnum, User
from app.utils import CrudException, UnitOfWork, get_uow
from app.utils.auth import user_has_permissions


__all__ = ["GenreService"]


class GenreService:
    @staticmethod
    async def get_genres(name: Optional[str], uow: UnitOfWork) -> List[Genre]:
        async with uow.begin():
            genres = await GenresRepository.get_multiple(uow.get_connection(), name)
            if genres is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            return genres

    @staticmethod
    async def get_genre(genre_id: int, uow: UnitOfWork) -> Genre:
        async with uow.begin():
            genre = await GenresRepository.get(uow.get_connection(), genre_id)
            if genre is None:
                raise HTTPException(status_code=404, detail="Genre not found")
            return genre

    @staticmethod
    async def create_genre(genre: GenreCreate, uow: UnitOfWork) -> int:
        async with uow.begin():
            key = await GenresRepository.get_multiple(uow.get_connection(), name=genre.name)
            if len(key) == 0:
                key = await GenresRepository.create(uow.get_connection(), genre)
            else:
                raise HTTPException(status_code=409, detail="Genre already exists")
            return key

    @staticmethod
    async def delete_genre(genre_id: int, uow: UnitOfWork) -> Genre:
        async with uow.begin():
            try:
                genre = await GenresRepository.delete(uow.get_connection(), genre_id)
                if genre is None:
                    raise HTTPException(status_code=404, detail="Genre not found")
                await uow.get_connection().commit()
                return genre
            except CrudException as e:
                raise HTTPException(status_code=404, detail=str(e))

    @staticmethod
    async def update_genre(genre_id: int, genre: GenreCreate, uow: UnitOfWork) -> Genre:
        async with uow.begin():
            try:
                genre = await GenresRepository.update(uow.get_connection(), genre_id, genre)
                if genre is None:
                    raise HTTPException(status_code=404, detail="Genre not found")
                await uow.get_connection().commit()
                return genre
            except CrudException as e:
                raise HTTPException(status_code=404, detail=str(e))
