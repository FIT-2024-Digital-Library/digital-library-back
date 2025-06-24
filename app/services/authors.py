from typing import List, Optional
from fastapi import HTTPException

from app.repositories import AuthorsRepository
from app.schemas import Author, AuthorCreate
from app.utils import CrudException, UnitOfWork


__all__ = ["AuthorService"]


class AuthorService:
    @staticmethod
    async def get_authors(name: Optional[str], uow: UnitOfWork) -> List[Author]:
        async with uow.begin():
            authors = await AuthorsRepository.get_multiple(uow.get_connection(), name)
            if authors is None:
                raise HTTPException(status_code=404, detail="Author not found")
            return authors

    @staticmethod
    async def get_author(author_id: int, uow: UnitOfWork) -> Author:
        async with uow.begin():
            author = await AuthorsRepository.get(uow.get_connection(), author_id)
            if author is None:
                raise HTTPException(status_code=404, detail="Author not found")
            return author

    @staticmethod
    async def create_author(author: AuthorCreate, uow: UnitOfWork) -> int:
        async with uow.begin():
            key = await AuthorsRepository.get_multiple(uow.get_connection(), name=author.name)
            if len(key) == 0:
                key = await AuthorsRepository.create(uow.get_connection(), author)
            else:
                raise HTTPException(status_code=409, detail="Author already exists")
            await uow.get_connection().commit()
            return key

    @staticmethod
    async def delete_author(author_id: int, uow: UnitOfWork) -> Author:
        async with uow.begin():
            try:
                author = await AuthorsRepository.delete(uow.get_connection(), author_id)
                if author is None:
                    raise HTTPException(status_code=404, detail="Author not found")
                await uow.get_connection().commit()
                return author
            except CrudException as e:
                raise HTTPException(status_code=404, detail=str(e))

    @staticmethod
    async def update_author(author_id: int, author: AuthorCreate, uow: UnitOfWork) -> Author:
        async with uow.begin():
            try:
                author = await AuthorsRepository.update(uow.get_connection(), author_id, author)
                if author is None:
                    raise HTTPException(status_code=404, detail="Author not found")
                await uow.get_connection().commit()
                return author
            except CrudException as e:
                raise HTTPException(status_code=404, detail=str(e))
