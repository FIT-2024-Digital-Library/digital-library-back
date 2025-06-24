from typing import Optional, List
from fastapi import HTTPException, BackgroundTasks

from app.repositories import BooksRepository, Indexing
from app.schemas import Book, BookCreate, BookUpdate, BookIndex
from app.utils import UnitOfWork


__all__ = ["BookService"]


class BookService:
    @staticmethod
    async def get_books(
            title: Optional[str],
            author: Optional[str],
            genre: Optional[str],
            published_date: Optional[int],
            description: Optional[str],
            min_mark: Optional[float],
            max_mark: Optional[float],
            uow: UnitOfWork
    ) -> List[int]:
        async with uow.begin():
            books = await BooksRepository.get_multiple(
                uow.get_connection(),
                title, author, genre, published_date, description, min_mark, max_mark
            )
            return books


    @staticmethod
    async def get_book(book_id: int, uow: UnitOfWork) -> Book:
        async with uow.begin():
            result = await BooksRepository.get(uow.get_connection(), book_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Book not found")
            return result


    @staticmethod
    async def create_book(
            book: BookCreate, background_tasks: BackgroundTasks, uow: UnitOfWork
    ) -> Book:
        async with uow.begin():
            book_added = await BooksRepository.create(uow.get_connection(), book)
            await uow.get_connection().commit()
            background_tasks.add_task(
                Indexing.index_book, book_added.id, BookIndex(**book_added.model_dump())
            )
            return book_added


    @staticmethod
    async def update_book(book_id: int, book: BookUpdate, uow: UnitOfWork) -> Book:
        async with uow.begin():
            book = await BooksRepository.update(uow.get_connection(), book_id, book)
            if book is None:
                raise HTTPException(status_code=404, detail="Book not found")
            return book


    @staticmethod
    async def delete_book(book_id: int, uow: UnitOfWork) -> Book:
        async with uow.begin():
            book = await BooksRepository.delete(uow.get_connection(), book_id)
            if book is None:
                raise HTTPException(status_code=404, detail="Book not found")
            return book
