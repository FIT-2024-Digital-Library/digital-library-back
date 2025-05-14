from typing import List, Optional
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.exc import IntegrityError

from app.crud.crud_interface import CrudInterface
from app.models import Author
from app.schemas import AuthorCreate
from app.utils import CrudException


class AuthorsCrud(CrudInterface):
    @classmethod
    async def get(cls, connection: AsyncConnection, author_id: int) -> Optional[Author]:
        result = await connection.execute(
            select(Author)
            .where(Author.id == author_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_multiple(
            cls,
            connection: AsyncConnection,
            name: Optional[str] = None
    ) -> List[Author]:
        query = select(Author)

        if name is not None:
            query = query.where(Author.name.ilike(f"%{name}%"))

        result = await connection.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, connection: AsyncConnection, author: AuthorCreate) -> int:
        result = await connection.execute(
            insert(Author)
            .values(name=author.name)
            .returning(Author.id)
        )
        return result.scalar_one()

    @classmethod
    async def get_existent_or_create(
            cls,
            connection: AsyncConnection,
            author: AuthorCreate
    ) -> int:
        existing_authors = await cls.get_multiple(connection, name=author.name)

        if existing_authors:
            return existing_authors[0].id

        result = await connection.execute(
            insert(Author)
            .values(name=author.name)
            .returning(Author.id)
        )
        return result.scalar_one()

    @classmethod
    async def delete(cls, connection: AsyncConnection, author_id: int) -> Optional[Author]:
        try:
            author = await cls.get(connection, author_id)
            if author:
                await connection.execute(
                    delete(Author)
                    .where(Author.id == author_id)
                )
            return author
        except IntegrityError as e:
            raise CrudException(
                "Cannot delete author - it is referenced by other records"
            )

    @classmethod
    async def update(
            cls,
            connection: AsyncConnection,
            author_id: int,
            author: AuthorCreate
    ) -> Optional[Author]:
        try:
            author_in_db = await cls.get(connection, author_id)
            if author_in_db:
                await connection.execute(
                    update(Author)
                    .where(Author.id == author_id)
                    .values(name=author.name)
                )
            return author_in_db
        except IntegrityError as e:
            raise CrudException(
                "Cannot update author - integrity constraint violation"
            )
