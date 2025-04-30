import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.crud.books import BooksCrud
from app.crud.crud_interface import CrudInterface
from app.models import Review, Book, User
from app.schemas import ReviewCreate, ReviewUpdate, ReviewsFiltersScheme, BookUpdate


class ReviewsCrud(CrudInterface):
    @classmethod
    async def get(cls, session: AsyncSession, element_id: int) -> Optional[Review]:
        """Получить отзыв по ID с загрузкой связанных данных"""
        result = await session.execute(
            select(Review)
            .where(Review.id == element_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_multiple(cls, session: AsyncSession, filters: ReviewsFiltersScheme = None) -> List[int]:
        """Получить список ID отзывов с фильтрацией"""
        if filters is None:
            filters = ReviewsFiltersScheme()

        query = select(Review.id)

        if filters.book_id is not None:
            query = query.where(Review.book_id == filters.book_id)
        if filters.owner_id is not None:
            query = query.where(Review.owner_id == filters.owner_id)

        query = query.limit(filters.limit).offset(filters.offset)

        result = await session.execute(query)
        return [review_id for (review_id,) in result.all()]

    @classmethod
    async def create(cls, session: AsyncSession, model: ReviewCreate, owner_id: int = None) -> Review:
        """Создать новый отзыв"""
        # Проверка существования книги
        book = await BooksCrud.get(session, model.book_id)
        if book is None:
            raise ValueError("Book for review not found")

        # Проверка на дубликат отзыва
        if await cls.check_review_by_user_and_book(session, owner_id, book.id):
            raise ValueError("Only one review for book from one user")

        # Создание отзыва
        review = Review(
            owner_id=owner_id,
            book_id=model.book_id,
            mark=model.mark,
            text=model.text,
            last_edit_date=datetime.date.today()
        )
        session.add(review)

        # Обновление среднего рейтинга книги
        await cls._update_book_rating(session, book, model.mark, increment=True)

        await session.commit()
        await session.refresh(review)
        return review

    @classmethod
    async def delete(cls, session: AsyncSession, review_id: int, owner_id: int = None) -> Review:
        """Удалить отзыв"""
        review = await cls.get(session, review_id)
        if review is None:
            raise ValueError("Review not found")
        if review.owner_id != owner_id:
            raise ValueError("It's not your review")

        # Получаем книгу перед удалением отзыва
        book = await BooksCrud.get(session, review.book_id)

        # Удаляем отзыв
        await session.delete(review)

        # Обновляем рейтинг книги
        await cls._update_book_rating(session, book, review.mark, increment=False)

        await session.commit()
        return review

    @classmethod
    async def update(cls, session: AsyncSession, element_id: int, owner_id: int, model: ReviewUpdate) -> Review:
        """Обновить отзыв"""
        review = await cls.get(session, element_id)
        if review is None:
            raise ValueError("Review not found")
        if review.owner_id != owner_id:
            raise ValueError("It's not your review")

        book = await BooksCrud.get(session, review.book_id)

        # Если меняется оценка - обновляем рейтинг книги
        if model.mark is not None and model.mark != review.mark:
            old_mark = review.mark
            review.mark = model.mark
            await cls._update_book_rating_change(session, book, old_mark, model.mark)

        if model.text is not None:
            review.text = model.text

        review.last_edit_date = datetime.date.today()
        await session.commit()
        await session.refresh(review)
        return review

    @classmethod
    async def check_review_by_user_and_book(cls, session: AsyncSession, owner_id: int, book_id: int) -> bool:
        """Проверить существование отзыва пользователя для книги"""
        result = await session.execute(
            select(Review)
            .where(
                Review.owner_id == owner_id,
                Review.book_id == book_id
            )
            .limit(1)
        )
        return result.scalar() is not None

    @classmethod
    async def get_average_mark(cls, session: AsyncSession, book_id: int) -> Optional[float]:
        """Получить средний рейтинг книги"""
        book = await BooksCrud.get(session, book_id)
        return book.avg_mark if book else None

    @classmethod
    async def get_reviews_count(cls, session: AsyncSession, book_id: int) -> Optional[int]:
        """Получить количество отзывов для книги"""
        book = await BooksCrud.get(session, book_id)
        return book.marks_count if book else None

    # Вспомогательные методы для работы с рейтингом
    @classmethod
    async def _update_book_rating(cls, session: AsyncSession, book: Book, mark: int, increment: bool = True):
        """Обновить рейтинг книги при добавлении/удалении отзыва"""
        current_avg = book.avg_mark or 0
        reviews_count = book.marks_count or 0

        if increment:
            new_count = reviews_count + 1
            new_avg = (current_avg * reviews_count + mark) / new_count
        else:
            new_count = reviews_count - 1
            new_avg = (current_avg * reviews_count - mark) / new_count if new_count > 0 else 0

        book.avg_mark = new_avg
        book.marks_count = new_count
        await session.flush()

    @classmethod
    async def _update_book_rating_change(cls, session: AsyncSession, book: Book, old_mark: int, new_mark: int):
        """Обновить рейтинг книги при изменении оценки в отзыве"""
        current_avg = book.avg_mark or 0
        reviews_count = book.marks_count or 0

        new_avg = (current_avg * reviews_count - old_mark + new_mark) / reviews_count
        book.avg_mark = new_avg
        await session.flush()
