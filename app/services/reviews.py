from typing import List
from fastapi import HTTPException

from app.repositories import ReviewsRepository
from app.schemas import User, ReviewsFiltersScheme, Review, ReviewCreate, ReviewUpdate
from app.utils import UnitOfWork


__all__ = ["ReviewService"]


class ReviewService:
    @staticmethod
    async def get_reviews(filters: ReviewsFiltersScheme, uow: UnitOfWork) -> List[int]:
        async with uow.begin():
            try:
                return await ReviewsRepository.get_multiple(uow.get_connection(), filters)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def get_review(review_id: int, uow: UnitOfWork) -> Review:
        async with uow.begin():
            result = await ReviewsRepository.get(uow.get_connection(), review_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Review not found")
            return result

    @staticmethod
    async def get_average_mark(book_id: int, uow: UnitOfWork) -> float:
        async with uow.begin():
            avg_mark = await ReviewsRepository.get_average_mark(uow.get_connection(), book_id)
            if avg_mark is None:
                raise HTTPException(status_code=404, detail="Book not found")
            return avg_mark

    @staticmethod
    async def get_marks_count(book_id: int, uow: UnitOfWork) -> int:
        async with uow.begin():
            reviews_count = await ReviewsRepository.get_reviews_count(uow.get_connection(), book_id)
            if reviews_count is None:
                raise HTTPException(status_code=404, detail="Book not found")
            return reviews_count

    @staticmethod
    async def create_review(review: ReviewCreate, user_creds: User, uow: UnitOfWork) -> Review:
        async with uow.begin():
            try:
                return await ReviewsRepository.create(uow.get_connection(), review, user_creds.id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def update_review(
            review_id: int, review: ReviewUpdate, user_creds: User, uow: UnitOfWork
    ) -> Review:
        async with uow.begin():
            try:
                return await ReviewsRepository.update(uow.get_connection(), review_id, user_creds.id, review)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def delete_review(review_id: int, user_creds: User, uow: UnitOfWork) -> Review:
        async with uow.begin():
            try:
                return await ReviewsRepository.delete(uow.get_connection(), review_id, user_creds.id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
