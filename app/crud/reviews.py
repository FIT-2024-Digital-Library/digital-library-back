from typing_extensions import Unpack

import datetime

from sqlalchemy import select, insert, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud.books import get_book_from_db
from app.models import review_table
from app.schemas import Review, ReviewCreate, ReviewUpdate, ReviewsFiltersScheme


async def get_reviews_in_db(session: AsyncSession, filters: ReviewsFiltersScheme) -> List[int]:
    query = select(review_table.c[*Review.model_fields]).limit(filters.limit).offset(filters.offset)
    if filters.book_id is not None:
        query = query.where(review_table.c.book_id == filters.book_id)
    if filters.owner_id is not None:
        query = query.where(review_table.c.owner_id == filters.owner_id)
    result = await session.execute(query)
    return [review['id'] for review in result.mappings().all()]


async def get_average_mark_in_db(session: AsyncSession, book_id: int) -> float:
    book = await get_book_from_db(session, book_id)
    if book is None:
        raise ValueError("Book not found")
    result = await session.execute(
        select(review_table.c.mark).where(review_table.c.book_id == book_id)
    )
    count = 0.0
    _sum = 0.0
    for review in result.mappings().all():
        _sum += review['mark']
        count += 1.0
    return _sum / count if count > 0 else 0


async def check_review_by_user_and_book(session: AsyncSession, owner_id: int, book_id: int) -> bool:
    """Returns true when there is review for specified combination of user and book ids"""
    result = (await session.execute((
        select(review_table)
        .where(
            review_table.c.owner_id == owner_id,
            review_table.c.book_id == book_id
        )
    ))).scalar()
    return result is not None


async def get_review_by_id(session: AsyncSession, review_id: int) -> Review:
    result = (await session.execute((
        select(review_table.c[*Review.model_fields])
        .where(review_table.c.id == review_id)
    ))).mappings().first()
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
        .returning(review_table.c[*Review.model_fields])
    )
    await session.commit()
    return Review(**result.mappings().first())


async def update_review_in_db(session: AsyncSession, review_id: int, owner_id: int, review_data: ReviewUpdate) -> Review:
    old_review = await get_review_by_id(session, review_id)
    if old_review is None:
        raise ValueError("Review not found")
    if old_review.owner_id is not owner_id:
        raise ValueError("It's not your review")
    result = await session.execute(
        update(review_table)
        .where(review_table.c.id == review_id)
        .values(last_edit_date=datetime.date.today(), **review_data.model_dump())
        .returning(review_table.c[*Review.model_fields])
    )
    await session.commit()
    return Review(**result.mappings().first())


async def delete_review_in_db(session: AsyncSession, review_id: int, owner_id: int) -> Review:
    review = await get_review_by_id(session, review_id)
    if review is None:
        raise ValueError("Review not found")
    if review.owner_id is not owner_id:
        raise ValueError("It's not your review")
    await session.execute(
        delete(review_table).where(review_table.c.id == review_id)
    )
    await session.commit()
    return review
