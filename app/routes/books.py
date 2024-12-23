import urllib.parse
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks

from app.crud.books import get_books_from_db, get_book_from_db, create_book_in_db, \
    update_book_in_db, delete_book_from_db
from app.crud import indexing
from app.crud.storage import delete_file_in_s3
from app.schemas import Book, BookCreate, User, BookUpdate, PrivilegesEnum
from app.settings import async_session_maker
from app.utils.auth import user_has_permissions


router = APIRouter(
    prefix='/books',
    tags=['book']
)


@router.get('/', response_model=List[int], summary='Returns books using search parameters (all of them otherwise)')
async def get_books(
        title: Optional[str] = Query(None, description="Filter by book title"),
        author: Optional[str] = Query(None, description="Filter by author"),
        genre: Optional[str] = Query(None, description="Filter by name"),
        published_date: Optional[int] = Query(None, description="Filter by publication year"),
        description: Optional[str] = Query(None, description="Filter by description keyword"),
        min_mark: Optional[float] = Query(
            None,
            description="Minimum mark (from 1 to 5 inclusive)",
            ge=1.0,
            le=5.0
        ),

        max_mark: Optional[float] = Query(
            None,
            description="Maximum mark (from 1 to 5 inclusive)",
            ge=1.0,
            le=5.0
        )
):
    async with async_session_maker() as session:
        books = await get_books_from_db(session, title, author, genre, published_date, description, min_mark, max_mark)
        return books


@router.get('/{book_id}', response_model=Book, summary='Returns book data')
async def get_book(book_id: int):
    async with async_session_maker() as session:
        result = await get_book_from_db(session, book_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return result


@router.post('/create', response_model=int,
             summary='Creates new book. Only for authorized user with moderator privilege')
async def create_book(
        book: BookCreate, background_tasks: BackgroundTasks,
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)
):
    async with async_session_maker() as session:
        book_id = await create_book_in_db(session, book)
        await session.commit()
        background_tasks.add_task(
            indexing.index_book, book_id, book.genre, urllib.parse.unquote(book.pdf_qname)
        )
        return book_id


@router.put('/{book_id}/update', response_model=Book,
            summary='Updates book data. Only for authorized user with admin privilege')
async def update_book(book_id: int, book: BookUpdate,
                      user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        book = await update_book_in_db(session, book_id, book)  ## тут тоже надо Celery
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        return book


@router.delete('/{book_id}/delete', response_model=Book,
               summary='Deletes book. Only for authorized user with admin privilege')
async def delete_book(book_id: int, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        book = await delete_book_from_db(session, book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        await indexing.delete_book(book_id)
        delete_file_in_s3(urllib.parse.unquote(book['pdf_qname']))
        return book
