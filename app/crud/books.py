import urllib.parse
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.authors import AuthorsCrud
from app.crud.crud_interface import CrudInterface
from app.crud.genres import GenresCrud
from app.crud.indexing import Indexing
from app.crud.storage import Storage
from app.models import Book, Author, Genre
from app.schemas import BookCreate, GenreCreate, AuthorCreate
from app.schemas.books import BookUpdate


class BooksCrud(CrudInterface):
    @classmethod
    async def get(cls, session: AsyncSession, element_id: int) -> Optional[Book]:
        """Получить книгу по ID с загрузкой связанных данных"""
        result = await session.execute(
            select(Book)
            .where(Book.id == element_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_multiple(
            cls,
            session: AsyncSession,
            title: Optional[str] = None,
            author: Optional[str] = None,
            genre: Optional[str] = None,
            published_date: Optional[int] = None,
            description: Optional[str] = None,
            min_mark: Optional[float] = None,
            max_mark: Optional[float] = None
    ) -> List[int]:
        """Получить список ID книг с фильтрацией"""
        query = select(Book.id)

        # Применяем фильтры
        filters = []
        if title:
            filters.append(Book.title.ilike(f"%{title}%"))
        if author:
            author_in_db = await AuthorsCrud.get_multiple(session, author)
            if not author_in_db:
                return []
            filters.append(Book.author == author_in_db[0].id)
        if genre:
            genre_in_db = await GenresCrud.get_multiple(session, genre)
            if not genre_in_db:
                return []
            filters.append(Book.genre == genre_in_db[0].id)
        if published_date:
            filters.append(Book.published_date == published_date)
        if description:
            filters.append(Book.description.ilike(f"%{description}%"))
        if min_mark is not None:
            filters.append(Book.avg_mark >= min_mark)
        if max_mark is not None:
            filters.append(Book.avg_mark <= max_mark)

        if filters:
            query = query.where(and_(*filters))

        result = await session.execute(query)
        return [book_id for (book_id,) in result.all()]

    @classmethod
    async def create(cls, session: AsyncSession, model: BookCreate) -> int:
        """Создать новую книгу"""
        book_data = model.model_dump()

        # Обработка жанра
        if book_data['genre']:
            genre_id = await GenresCrud.get_existent_or_create(
                session,
                GenreCreate(name=book_data['genre'])
            )
            book_data['genre'] = genre_id

        # Обработка автора
        author_id = await AuthorsCrud.get_existent_or_create(
            session,
            AuthorCreate(name=book_data['author'])
        )
        book_data['author'] = author_id

        # Создание книги
        book = Book(**book_data)
        session.add(book)
        await session.flush()
        return book.id

    @classmethod
    async def delete(cls, session: AsyncSession, element_id: int) -> Optional[Book]:
        """Удалить книгу"""
        book = await cls.get(session, element_id)
        if not book:
            return None

        # Удаление связанных файлов
        if book.pdf_qname:
            await Indexing.delete_book(element_id)
            Storage.delete_file_in_s3(urllib.parse.unquote(book.pdf_qname))
        if book.image_qname:
            Storage.delete_file_in_s3(urllib.parse.unquote(book.image_qname))

        await session.delete(book)
        await session.commit()
        return book

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            element_id: int,
            model: BookUpdate
    ) -> Optional[Book]:
        """Обновить информацию о книге"""
        book = await cls.get(session, element_id)
        if not book:
            return None

        update_data = model.model_dump(exclude_unset=True)

        # Обработка PDF файла
        if 'pdf_qname' in update_data and update_data['pdf_qname'] != book.pdf_qname:
            if book.pdf_qname:
                await Indexing.delete_book(element_id)
                Storage.delete_file_in_s3(urllib.parse.unquote(book.pdf_qname))

            if update_data['pdf_qname']:
                genre = update_data.get('genre', book.genre)
                await Indexing.index_book(
                    element_id,
                    genre,
                    urllib.parse.unquote(update_data['pdf_qname'])
                )

        # Обработка изображения
        if 'image_qname' in update_data and update_data['image_qname'] != book.image_qname:
            if book.image_qname:
                Storage.delete_file_in_s3(urllib.parse.unquote(book.image_qname))

        # Обработка жанра
        if 'genre' in update_data and update_data['genre']:
            genre_id = await GenresCrud.get_existent_or_create(
                session,
                GenreCreate(name=update_data['genre'])
            )
            update_data['genre'] = genre_id

        # Обработка автора
        if 'author' in update_data and update_data['author']:
            author_id = await AuthorsCrud.get_existent_or_create(
                session,
                AuthorCreate(name=update_data['author'])
            )
            update_data['author'] = author_id

        # Обновление полей
        for key, value in update_data.items():
            setattr(book, key, value)

        await session.commit()
        return book
