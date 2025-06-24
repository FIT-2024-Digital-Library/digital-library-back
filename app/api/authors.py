from typing import List, Optional
from fastapi import APIRouter, Query, Depends

from app.schemas import Author, AuthorCreate, PrivilegesEnum, User
from app.utils import UnitOfWork, get_uow
from app.utils.auth import user_has_permissions
from app.services import AuthorService


router = APIRouter(
    prefix='/authors',
    tags=['authors']
)


@router.get('/', response_model=List[Author], summary='Returns authors')
async def get_authors(
        name: Optional[str] = Query(None, description="Find by author name"),
        uow: UnitOfWork = Depends(get_uow)
):
    return await AuthorService.get_authors(name, uow)


@router.get('/{author_id}', response_model=Author, summary='Returns author')
async def get_author(author_id: int, uow: UnitOfWork = Depends(get_uow)):
    return await AuthorService.get_author(author_id, uow)


@router.post('/create', response_model=int, summary='Creates authors')
async def create_author(
        author: AuthorCreate,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await AuthorService.create_author(author, uow)


@router.delete('/{author_id}/delete', response_model=Author, summary='Deletes authors')
async def delete_author(
        author_id: int,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await AuthorService.delete_author(author_id, uow)


@router.put('/{author_id}/update', response_model=Author, summary='Updates authors')
async def update_author(
        author_id: int, author: AuthorCreate,
        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
        uow: UnitOfWork = Depends(get_uow)
):
    return await AuthorService.update_author(author_id, author, uow)
