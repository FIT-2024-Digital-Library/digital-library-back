from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends

from app.crud.books import get_books_from_db, get_book_from_db, create_book_in_db, \
    update_book_in_db, delete_book_from_db
from app.schemas import Book, BookCreate, User
from app.settings import async_session_maker
from app.utils.auth import get_current_user, get_current_admin_user

router = APIRouter(
    prefix='/books',
    tags=['book']
)


@router.get('/', response_model=List[Book], summary='Returns books using search parameters (all of them otherwise)')
async def get_books(
        title: Optional[str] = Query(None, description="Filter by book title"),
        author: Optional[str] = Query(None, description="Filter by author"),
        genre: Optional[str] = Query(None, description="Filter by name"),
        published_date: Optional[date] = Query(None, description="Filter by publication date"),
        description: Optional[str] = Query(None, description="Filter by description keyword"),
        image_url: Optional[str] = Query(None, description="Filter by image\'s URL"),
        pdf_url: Optional[str] = Query(None, description="Filter by PDF URL")
):
    async with async_session_maker() as session:
        books = await get_books_from_db(session, title, author, genre, published_date, description, image_url, pdf_url)
        return books


@router.get('/{book_id}', response_model=Book, summary='Returns book data')
async def get_book(book_id: int):
    async with async_session_maker() as session:
        result = await get_book_from_db(session, book_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return result


@router.post('/create', response_model=int, summary='Creates new book. Only for authorized user with admin privilege')
async def create_book(book: BookCreate, user_data: User = Depends(get_current_admin_user)):
    async with async_session_maker() as session:
        book_id = await create_book_in_db(session, book)
        await session.commit()
        return book_id


@router.put('/{book_id}/update', response_model=Book,
            summary='Updates book data. Only for authorized user with admin privilege')
async def update_book(book_id: int, book: BookCreate, user_data: User = Depends(get_current_admin_user)):
    async with async_session_maker() as session:
        book = await update_book_in_db(session, book_id, book)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        return book


@router.delete('/{book_id}/delete', response_model=Book,
               summary='Deletes book. Only for authorized user with admin privilege')
async def delete_book(book_id: int, user_data: User = Depends(get_current_admin_user)):
    async with async_session_maker() as session:
        book = await delete_book_from_db(session, book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.commit()
        return book
