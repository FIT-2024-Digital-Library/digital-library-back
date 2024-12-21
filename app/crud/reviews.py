from typing_extensions import Unpack
import datetime
from sqlalchemy import select, insert, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.crud.books import get_book_from_db, update_book_in_db
from app.models import review_table
from app.schemas import Review, ReviewCreate, ReviewUpdate, ReviewsFiltersScheme


async def get_reviews_in_db(session: AsyncSession, filters: ReviewsFiltersScheme) -> List[int]:
    query = select(review_table.c[Unpack[Review.model_fields]]).limit(filters.limit).offset(filters.offset)
    if filters.book_id is not None:
        query = query.where(review_table.c.book_id == filters.book_id)
    if filters.owner_id is not None:
        query = query.where(review_table.c.owner_id == filters.owner_id)
    result = await session.execute(query)
    return [review['id'] for review in result.mappings().all()]


async def get_average_mark_in_db(session: AsyncSession, book_id: int) -> Optional[float]:
    book = await get_book_from_db(session, book_id)
    return book['avg_mark'] if book else None


async def check_review_by_user_and_book(session: AsyncSession, owner_id: int, book_id: int) -> bool:
    result = (await session.execute(
        select(review_table)
        .where(
            review_table.c.owner_id == owner_id,
            review_table.c.book_id == book_id
        )
    )).scalar()
    return result is not None


async def get_review_by_id(session: AsyncSession, review_id: int) -> Optional[Review]:
    result = (await session.execute(
        select(review_table.c[Unpack[Review.model_fields]])
        .where(review_table.c.id == review_id)
    )).mappings().first()
    return None if result is None else Review(**result)


async def create_review_in_db(session: AsyncSession, owner_id: int, review_data: ReviewCreate) -> Review:
    book = await get_book_from_db(session, review_data.book_id)
    if book is None:
        raise ValueError("Book for review not found")
    if await check_review_by_user_and_book(session, owner_id, book['id']):
        raise ValueError("Only one review for book from one user")
    result = await session.execute(
        insert(review_table)
        .values(owner_id=owner_id, last_edit_date=datetime.date.today(), **review_data.model_dump())
        .returning(review_table.c[Unpack[Review.model_fields]])
    )
    current_avg = book['avg_mark']
    reviews_count_for_book = book['marks_count']
    new_reviews_count = reviews_count_for_book + 1
    new_avg = (current_avg * reviews_count_for_book + review_data.mark) / new_reviews_count
    await update_book_in_db(session, review_data.book_id,
                            {'avg_mark': new_avg, 'marks_count': new_reviews_count})
    await session.commit()
    return Review(**result.mappings().first())


async def update_review_in_db(session: AsyncSession, review_id: int, owner_id: int,
                              review_data: ReviewUpdate) -> Review:
    old_review = await get_review_by_id(session, review_id)
    if old_review is None:
        raise ValueError("Review not found")
    if old_review.owner_id != owner_id:
        raise ValueError("It's not your review")
    if review_data.mark is not None and review_data.mark != old_review.mark:
        book = await get_book_from_db(session, old_review.book_id)
        current_avg = book['avg_mark']
        reviews_count_for_book = book['marks_count']
        new_avg = (current_avg * reviews_count_for_book - old_review.mark + review_data.mark) / reviews_count_for_book
        await update_book_in_db(session, old_review.book_id, {'avg_mark': new_avg})
    result = await session.execute(
        update(review_table)
        .where(review_table.c.id == review_id)
        .values(last_edit_date=datetime.date.today(), **review_data.model_dump())
        .returning(review_table.c[Unpack[Review.model_fields]])
    )
    await session.commit()
    return Review(**result.mappings().first())


async def delete_review_in_db(session: AsyncSession, review_id: int, owner_id: int) -> Review:
    review = await get_review_by_id(session, review_id)
    if review is None:
        raise ValueError("Review not found")
    if review.owner_id != owner_id:
        raise ValueError("It's not your review")
    book = await get_book_from_db(session, review.book_id)
    current_avg = book['avg_mark']
    reviews_count_for_book = book['marks_count']
    new_reviews_count = reviews_count_for_book - 1
    new_avg = (current_avg * reviews_count_for_book - review.mark) / new_reviews_count if new_reviews_count > 0 else 0
    await update_book_in_db(session, review.book_id,
                            {'avg_mark': new_avg, 'marks_count': new_reviews_count})
    await session.execute(
        delete(review_table).where(review_table.c.id == review_id)
    )
    await session.commit()
    return review
