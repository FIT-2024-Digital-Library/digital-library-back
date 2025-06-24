from typing import Optional, List
from fastapi import APIRouter, Query, BackgroundTasks, Depends

from app.schemas import Book, BookCreate, User, BookUpdate, PrivilegesEnum
from app.services import BookService
from app.utils import get_uow, UnitOfWork
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
        ),
        uow: UnitOfWork = Depends(get_uow)
):
    return await BookService.get_books(
        title, author, genre, published_date, description, min_mark, max_mark, uow
    )


@router.get('/{book_id}', response_model=Book, summary='Returns book data')
async def get_book(book_id: int, uow: UnitOfWork = Depends(get_uow)):
    return await BookService.get_book(book_id, uow)


@router.post('/create', response_model=Book,
             summary='Creates new book. Only for authorized user with moderator privilege')
async def create_book(
        book: BookCreate, background_tasks: BackgroundTasks,
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await BookService.create_book(book, background_tasks, uow)


@router.put('/{book_id}/update', response_model=Book,
            summary='Updates book data. Only for authorized user with admin privilege')
async def update_book(
        book_id: int, book: BookUpdate,
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await BookService.update_book(book_id, book, uow)


@router.delete('/{book_id}/delete', response_model=Book,
               summary='Deletes book. Only for authorized user with admin privilege')
async def delete_book(
        book_id: int,
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await BookService.delete_book(book_id, uow)
