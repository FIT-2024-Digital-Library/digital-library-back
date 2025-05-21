from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.crud.authors import AuthorsCrud
from app.schemas import Author, AuthorCreate, PrivilegesEnum, User
from app.utils import CrudException
from app.utils.auth import user_has_permissions
from app.utils.unit_of_work import UnitOfWork, get_uow

router = APIRouter(
    prefix='/authors',
    tags=['authors']
)


@router.get('/', response_model=List[Author], summary='Returns authors')
async def get_authors(name: Optional[str] = Query(None, description="Find by author name"),
                      uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        authors = await AuthorsCrud.get_multiple(uow.get_connection(), name)
        if authors is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return authors


@router.get('/{author_id}', response_model=Author, summary='Returns author')
async def get_author(author_id: int, uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        author = await AuthorsCrud.get(uow.get_connection(), author_id)
        if author is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return author


@router.post('/create', response_model=int, summary='Creates authors')
async def create_author(author: AuthorCreate,
                        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                        uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        key = await AuthorsCrud.get_multiple(uow.get_connection(), name=author.name)
        if len(key) == 0:
            key = await AuthorsCrud.create(uow.get_connection(), author)
        else:
            raise HTTPException(status_code=409, detail="Author already exists")
        await uow.get_connection().commit()
        return key


@router.delete('/{author_id}/delete', response_model=Author, summary='Deletes authors')
async def delete_author(author_id: int,
                        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                        uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        try:
            author = await AuthorsCrud.delete(uow.get_connection(), author_id)
            if author is None:
                raise HTTPException(status_code=404, detail="Author not found")
            await uow.get_connection().commit()
            return author
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.put('/{author_id}/update', response_model=Author, summary='Updates authors')
async def update_author(author_id: int, author: AuthorCreate,
                        user_creds: User = user_has_permissions(PrivilegesEnum.MODERATOR),
                        uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        try:
            author = await AuthorsCrud.update(uow.get_connection(), author_id, author)
            if author is None:
                raise HTTPException(status_code=404, detail="Author not found")
            await uow.get_connection().commit()
            return author
        except CrudException as e:
            raise HTTPException(status_code=404, detail=str(e))
