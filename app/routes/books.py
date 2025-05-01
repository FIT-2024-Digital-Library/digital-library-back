import urllib.parse
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks

from app.crud.books import BooksCrud
from app.crud.indexing import Indexing
from app.crud.storage import Storage
from app.schemas import BookCreate, Book, User, BookUpdate, PrivilegesEnum
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
        books = await BooksCrud.get_multiple(session, title, author, genre, published_date, description, min_mark,
                                             max_mark)
        return books


@router.get('/{book_id}', response_model=Book, summary='Returns book data')
async def get_book(book_id: int):
    async with async_session_maker() as session:
        result = await BooksCrud.get(session, book_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return result


@router.post('/create', response_model=Book,
             summary='Creates new book. Only for authorized user with moderator privilege')
async def create_book(
        book: BookCreate, background_tasks: BackgroundTasks,
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)
):
    async with async_session_maker() as session:
        book_id = await BooksCrud.create(session, book)
        await session.commit()
        background_tasks.add_task(
            Indexing.index_book, book_id, book.genre, urllib.parse.unquote(book.pdf_qname)
        )
        return book_id


@router.put('/{book_id}/update', response_model=Book,
            summary='Updates book data. Only for authorized user with admin privilege')
async def update_book(book_id: int, book: BookUpdate,
                      user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        book = await BooksCrud.update(session, book_id, book)  ## тут тоже надо Celery
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        return book


@router.delete('/{book_id}/delete', response_model=Book,
               summary='Deletes book. Only for authorized user with admin privilege')
async def delete_book(book_id: int, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    async with async_session_maker() as session:
        book = await BooksCrud.delete(session, book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        await Indexing.delete_book(book_id)
        Storage.delete_file_in_s3(urllib.parse.unquote(book['pdf_qname']))
        if book['image_qname'] is not None and book['image_qname'] != "":
            Storage.delete_file_in_s3(urllib.parse.unquote(book['image_qname']))
        return book
