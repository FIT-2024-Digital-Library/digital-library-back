import urllib.parse
from typing import List, Optional
from sqlalchemy import select, and_, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncConnection

from app import models
from app.schemas import Book, BookCreate, BookUpdate, BookIndex, GenreCreate, AuthorCreate

from .authors import AuthorsRepository
from .base import SQLAlchemyRepository
from .genres import GenresRepository
from .indexing import Indexing
from .storage import Storage


__all__ = ["BooksRepository"]


class BooksRepository(SQLAlchemyRepository):
    @classmethod
    async def get(cls, connection: AsyncConnection, element_id: int) -> Optional[Book]:
        result = await connection.execute(
            select(models.Book)
            .where(models.Book.id == element_id)
        )
        book_model = result.mappings().first()
        author = await AuthorsRepository.get(connection, book_model.author)
        author_name = author and author.name
        genre = await GenresRepository.get(connection, book_model.genre)
        genre_name = genre and genre.name
        return Book(
            id=book_model.id, theme_id=book_model.theme_id, title=book_model.title,
            author=author_name, genre=genre_name, published_date=book_model.published_date,
            description=book_model.description, image_qname=book_model.image_qname,
            pdf_qname=book_model.pdf_qname, avg_mark=book_model.avg_mark,
            marks_count=book_model.marks_count
        )

    @classmethod
    async def get_multiple(
            cls,
            connection: AsyncConnection,
            title: Optional[str] = None,
            author: Optional[str] = None,
            genre: Optional[str] = None,
            published_date: Optional[int] = None,
            description: Optional[str] = None,
            min_mark: Optional[float] = None,
            max_mark: Optional[float] = None
    ) -> List[int]:
        query = select(models.Book.id)
        filters = []
        if title:
            filters.append(models.Book.title.ilike(f"%{title}%"))
        if author:
            author_in_db = await AuthorsRepository.get_multiple(connection, author)
            if not author_in_db:
                return []
            filters.append(models.Book.author == author_in_db[0].id)
        if genre:
            genre_in_db = await GenresRepository.get_multiple(connection, genre)
            if not genre_in_db:
                return []
            filters.append(models.Book.genre == genre_in_db[0].id)
        if published_date:
            filters.append(models.Book.published_date == published_date)
        if description:
            filters.append(models.Book.description.ilike(f"%{description}%"))
        if min_mark is not None:
            filters.append(models.Book.avg_mark >= min_mark)
        if max_mark is not None:
            filters.append(models.Book.avg_mark <= max_mark)

        if filters:
            query = query.where(and_(*filters))

        result = await connection.execute(query)
        return [book_id for (book_id,) in result.all()]

    @classmethod
    async def create(cls, connection: AsyncConnection, model: BookCreate) -> Optional[Book]:
        book_data = model.model_dump()

        if book_data['genre']:
            genre_id = await GenresRepository.get_existent_or_create(
                connection,
                GenreCreate(name=book_data['genre'])
            )
            book_data['genre'] = genre_id

        author_id = await AuthorsRepository.get_existent_or_create(
            connection,
            AuthorCreate(name=book_data['author'])
        )
        book_data['author'] = author_id

        result = await connection.execute(insert(models.Book).values(**book_data).returning(models.Book.id))
        return await cls.get(connection, result.scalar())


    @classmethod
    async def delete(cls, connection: AsyncConnection, element_id: int) -> Optional[Book]:
        book = await cls.get(connection, element_id)
        if not book:
            return None

        if book.pdf_qname:
            await Indexing.delete_book(element_id)
            Storage.delete_file_in_s3(urllib.parse.unquote(book.pdf_qname))

        if book.image_qname:
            Storage.delete_file_in_s3(urllib.parse.unquote(book.image_qname))

        await connection.execute(delete(models.Book).where(models.Book.id == element_id))
        return book

    @classmethod
    async def update(
            cls,
            connection: AsyncConnection,
            element_id: int,
            model: BookUpdate
    ) -> Optional[Book]:
        book = await cls.get(connection, element_id)
        if not book:
            return None

        update_data = model.model_dump(exclude_unset=True)

        if 'pdf_qname' in update_data and update_data['pdf_qname'] != book['pdf_qname']:
            if book['pdf_qname']:
                await Indexing.delete_book(element_id)
                Storage.delete_file_in_s3(urllib.parse.unquote(book['pdf_qname']))

            if update_data['pdf_qname']:
                await Indexing.index_book(element_id, BookIndex(**update_data))

        if 'image_qname' in update_data and update_data['image_qname'] != book['image_qname']:
            if book['image_qname']:
                Storage.delete_file_in_s3(urllib.parse.unquote(book['image_qname']))

        if 'genre' in update_data and update_data['genre']:
            genre_id = await GenresRepository.get_existent_or_create(
                connection,
                GenreCreate(name=update_data['genre'])
            )
            update_data['genre'] = genre_id

        if 'author' in update_data and update_data['author']:
            author_id = await AuthorsRepository.get_existent_or_create(
                connection,
                AuthorCreate(name=update_data['author'])
            )
            update_data['author'] = author_id

        for key, value in update_data.items():
            if update_data[key] is None:
                update_data[key] = update_data[key]

        query = update(models.Book).where(models.Book.id == element_id).values(**update_data)
        await connection.execute(query)

        return await cls.get(connection, element_id)
