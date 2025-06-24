import datetime
from typing import List, Optional
from sqlalchemy import select, delete, update, insert
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.crud.books import BooksCrud
from app.crud.crud_interface import CrudInterface
from app.models import Review, Book, User
from app.schemas import ReviewCreate, ReviewUpdate, ReviewsFiltersScheme, BookUpdate


class ReviewsCrud(CrudInterface):
    @classmethod
    async def get(cls, connection: AsyncConnection, element_id: int) -> Optional[Review]:
        result = await connection.execute(
            select(Review)
            .where(Review.id == element_id)
        )
        return result.mappings().first()

    @classmethod
    async def get_multiple(cls, connection: AsyncConnection, filters: ReviewsFiltersScheme = None) -> List[int]:
        if filters is None:
            filters = ReviewsFiltersScheme()

        query = select(Review.id)

        if filters.book_id is not None:
            query = query.where(Review.book_id == filters.book_id)
        if filters.owner_id is not None:
            query = query.where(Review.owner_id == filters.owner_id)

        query = query.limit(filters.limit).offset(filters.offset)

        result = await connection.execute(query)
        return [review['id'] for review in result.mappings().all()]

    @classmethod
    async def create(cls, connection: AsyncConnection, model: ReviewCreate, owner_id: int = None) -> Review:
        book = await BooksCrud.get(connection, model.book_id)
        if book is None:
            raise ValueError("Book for review not found")

        if await cls.check_review_by_user_and_book(connection, owner_id, book.id):
            raise ValueError("Only one review for book from one user")

        result = await connection.execute(
            insert(Review).values(
                owner_id=owner_id,
                book_id=model.book_id,
                mark=model.mark,
                text=model.text,
                last_edit_date=datetime.date.today()
            ).returning(Review.__table__)
        )
        review_data = result.mappings().first()
        review = Review(**review_data)

        await cls._update_book_rating(connection, book, model.mark, increment=True)
        return review

    @classmethod
    async def delete(cls, connection: AsyncConnection, review_id: int, owner_id: int = None) -> Review:
        review = await cls.get(connection, review_id)
        if review is None:
            raise ValueError("Review not found")
        if review.owner_id != owner_id:
            raise ValueError("It's not your review")
        book = await BooksCrud.get(connection, review.book_id)
        await connection.execute(delete(Review).where(Review.id == review_id))
        await cls._update_book_rating(connection, book, review.mark, increment=False)
        return review

    @classmethod
    async def update(cls, connection: AsyncConnection, element_id: int, owner_id: int, model: ReviewUpdate) -> Review:
        review = await cls.get(connection, element_id)
        if review is None:
            raise ValueError("Review not found")
        if review['owner_id'] != owner_id:
            raise ValueError("It's not your review")
        update_values = model.model_dump(exclude_unset=True)

        book = await BooksCrud.get(connection, review.book_id)
        if model.mark is not None and model.mark != review['mark']:
            old_mark = review['mark']
            update_values['mark'] = model.mark
            await cls._update_book_rating_change(connection, book, old_mark, model.mark)

        if model.text is not None:
            update_values['text'] = model.text

        update_values['last_edit_date'] = datetime.date.today()

        # Execute the update
        await connection.execute(
            update(Review)
            .where(Review.id == element_id)
            .values(**update_values)
        )

        # Refresh and return the updated review
        result = await connection.execute(
            select(Review)
            .where(Review.id == element_id)
        )

        return Review(**result.mappings().first())

    @classmethod
    async def check_review_by_user_and_book(cls, connection: AsyncConnection, owner_id: int, book_id: int) -> bool:
        result = await connection.execute(
            select(Review)
            .where(
                Review.owner_id == owner_id,
                Review.book_id == book_id
            )
            .limit(1)
        )
        return result.scalar() is not None

    @classmethod
    async def get_average_mark(cls, connection: AsyncConnection, book_id: int) -> Optional[float]:
        book = await BooksCrud.get(connection, book_id)
        return book.avg_mark if book else None

    @classmethod
    async def get_reviews_count(cls, connection: AsyncConnection, book_id: int) -> Optional[int]:
        book = await BooksCrud.get(connection, book_id)
        return book.marks_count if book else None

    @classmethod
    async def _update_book_rating(cls, connection: AsyncConnection, book: Book, mark: int, increment: bool = True):
        current_avg = book['avg_mark']
        reviews_count_for_book = book['marks_count']
        if increment:
            new_reviews_count = reviews_count_for_book + 1
            new_avg = (current_avg * reviews_count_for_book + mark) / new_reviews_count
        else:
            new_reviews_count = reviews_count_for_book - 1
            if new_reviews_count == 0:
                new_avg = 0
            else:
                new_avg = (current_avg * reviews_count_for_book - mark) / new_reviews_count
        await BooksCrud.update(connection, book['id'],
                               BookUpdate(**{'avg_mark': new_avg, 'marks_count': new_reviews_count}))

    @classmethod
    async def _update_book_rating_change(cls, connection: AsyncConnection, book: Book, old_mark: int, new_mark: int):
        current_avg = book['avg_mark'] or 0
        reviews_count = book['marks_count'] or 0
        new_avg = (current_avg * reviews_count - old_mark + new_mark) / reviews_count

        await BooksCrud.update(connection, book['id'],
                               BookUpdate(**{'avg_mark': new_avg}))
