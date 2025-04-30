from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.crud_interface import CrudInterface
from app.models import Author
from app.schemas import AuthorCreate
from app.utils import CrudException


class AuthorsCrud(CrudInterface):
    @classmethod
    async def get(cls, session: AsyncSession, author_id: int) -> Optional[Author]:
        result = await session.execute(
            select(Author)
            .where(Author.id == author_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_multiple(
            cls,
            session: AsyncSession,
            name: Optional[str] = None
    ) -> List[Author]:
        query = select(Author)

        if name is not None:
            query = query.where(Author.name.ilike(f"%{name}%"))

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, author: AuthorCreate) -> int:
        """Создать нового автора"""
        new_author = Author(name=author.name)
        session.add(new_author)
        await session.flush()
        return new_author.id

    @classmethod
    async def get_existent_or_create(
            cls,
            session: AsyncSession,
            author: AuthorCreate
    ) -> int:
        existing_authors = await cls.get_multiple(session, name=author.name)

        if existing_authors:
            return existing_authors[0].id

        new_author = Author(name=author.name)
        session.add(new_author)
        await session.flush()
        return new_author.id

    @classmethod
    async def delete(cls, session: AsyncSession, author_id: int) -> Optional[Author]:
        try:
            author = await cls.get(session, author_id)
            if author:
                await session.delete(author)
                await session.flush()
            return author
        except IntegrityError as e:
            await session.rollback()
            raise CrudException(
                "Cannot delete author - it is referenced by other records"
            )

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            author_id: int,
            author: AuthorCreate
    ) -> Optional[Author]:
        try:
            author_in_db = await cls.get(session, author_id)
            if author_in_db:
                author_in_db.name = author.name
                await session.flush()
                await session.refresh(author_in_db)
            return author_in_db
        except IntegrityError as e:
            await session.rollback()
            raise CrudException(
                "Cannot update author - integrity constraint violation"
            )
