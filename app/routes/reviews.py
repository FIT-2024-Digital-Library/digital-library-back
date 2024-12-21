from typing import List, Annotated
from fastapi import APIRouter, Query, HTTPException, Depends

from app.crud.reviews import get_review_by_id, create_review_in_db, update_review_in_db, delete_review_in_db, \
    get_reviews_in_db, get_average_mark_in_db
from app.schemas import User, ReviewsFiltersScheme, Review, ReviewCreate, ReviewUpdate
from app.settings import async_session_maker
from app.utils.auth import get_current_user


router = APIRouter(
    prefix='/reviews',
    tags=['review']
)


@router.get('/', response_model=List[int], summary="Returns reviews's ids maybe filtered by book and user")
async def get_reviews(filters: Annotated[ReviewsFiltersScheme, Query()]) -> List[int]:
    async with async_session_maker() as session:
        try:
            return await get_reviews_in_db(session, filters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get('/{review_id}', response_model=Review, summary='Returns review')
async def get_review(review_id: int) -> Review:
    async with async_session_maker() as session:
        result = await get_review_by_id(session, review_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Review not found")
        return result


@router.get('/average/{book_id}', response_model=float, summary='Returns average mark for book')
async def get_average_mark(book_id: int) -> float:
    async with async_session_maker() as session:
        try:
            return await get_average_mark_in_db(session, book_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post('/create', response_model=Review,
             summary='Creates new review. Only for authorized users. One review from one user for one book')
async def create_review(review: ReviewCreate, user_creds: User = Depends(get_current_user)) -> Review:
    async with async_session_maker() as session:
        try:
            return await create_review_in_db(session, user_creds.id, review)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.put('/{review_id}/update', response_model=Review, summary="Updates existing review. Only for reviews' owners")
async def update_review(review_id: int, review: ReviewUpdate, user_creds: User = Depends(get_current_user)) -> Review:
    async with async_session_maker() as session:
        try:
            return await update_review_in_db(session, review_id, user_creds.id, review)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete('/{review_id}/delete', response_model=Review,
               summary="Deletes existing review. Only for reviews' owners")
async def delete_review(review_id: int, user_creds: User = Depends(get_current_user)) -> Review:
    async with async_session_maker() as session:
        try:
            return await delete_review_in_db(session, review_id, user_creds.id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
