from typing import List, Annotated
from fastapi import APIRouter, Query, Depends

from app.schemas import User, ReviewsFiltersScheme, Review, ReviewCreate, ReviewUpdate
from app.services import ReviewService
from app.utils import UnitOfWork, get_uow
from app.utils.auth import get_current_user


router = APIRouter(
    prefix='/reviews',
    tags=['review']
)


@router.get('/', response_model=List[int],
            summary="Returns reviews's ids maybe filtered by book and user")
async def get_reviews(
        filters: Annotated[ReviewsFiltersScheme, Query()], uow: UnitOfWork = Depends(get_uow)
) -> List[int]:
    return await ReviewService.get_reviews(filters, uow)


@router.get('/{review_id}', response_model=Review, summary='Returns review')
async def get_review(review_id: int, uow: UnitOfWork = Depends(get_uow)) -> Review:
    return await ReviewService.get_review(review_id, uow)


@router.get('/average/{book_id}', response_model=float, summary='Returns average mark for book')
async def get_average_mark(book_id: int, uow: UnitOfWork = Depends(get_uow)) -> float:
    return await ReviewService.get_average_mark(book_id, uow)


@router.get('/count/{book_id}', response_model=int, summary='Returns marks count for book')
async def get_marks_count(book_id: int, uow: UnitOfWork = Depends(get_uow)) -> int:
    return await ReviewService.get_marks_count(book_id, uow)


@router.post('/create', response_model=Review,
             summary='Creates new review. Only for authorized users. One review from one user for one book')
async def create_review(
        review: ReviewCreate,
        user_creds: User = Depends(get_current_user),
        uow: UnitOfWork = Depends(get_uow)
) -> Review:
    return await ReviewService.create_review(review, user_creds, uow)


@router.put('/{review_id}/update', response_model=Review,
            summary="Updates existing review. Only for reviews' owners")
async def update_review(
        review_id: int, review: ReviewUpdate,
        user_creds: User = Depends(get_current_user),
        uow: UnitOfWork = Depends(get_uow)
) -> Review:
    return await ReviewService.update_review(review_id, review, user_creds, uow)


@router.delete('/{review_id}/delete', response_model=Review,
               summary="Deletes existing review. Only for reviews' owners")
async def delete_review(
        review_id: int,
        user_creds: User = Depends(get_current_user),
        uow: UnitOfWork = Depends(get_uow)
) -> Review:
    return await ReviewService.delete_review(review_id, user_creds, uow)
