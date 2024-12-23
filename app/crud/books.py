import urllib.parse
from datetime import date
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.authors import get_existent_or_create_author_in_db, get_authors_from_db
from app.crud.genres import get_existent_or_create_genre_in_db, get_genres_from_db
from app.crud.indexing import delete_book, index_book
from app.crud.storage import delete_file_in_s3
from app.models import book_table
from app.schemas import BookCreate, GenreCreate, AuthorCreate
from app.schemas.books import BookUpdate


async def get_books_from_db(
        session: AsyncSession,
        title: str = None,
        author: str = None,
        genre: str = None,
        published_date: int = None,
        description: str = None,
        min_mark: float = None,
        max_mark: float = None):
    query = select(book_table.c.id)
    if title is not None:
        query = query.where(book_table.c.title.ilike(f"%{title}%"))
    if author is not None:
        author_in_db = await get_authors_from_db(session, author)
        if not author_in_db:
            return []
        author_id: int = author_in_db[0].get("id")
        query = query.where(book_table.c.author == author_id)
    if genre is not None:
        genre_in_db = await get_genres_from_db(session, genre)
        if not genre_in_db:
            return []
        genre_id: int = genre_in_db[0].get("id")
        query = query.where(book_table.c.genre == genre_id)
    if published_date is not None:
        query = query.where(book_table.c.published_date == published_date)
    if description is not None:
        query = query.where(book_table.c.description.ilike(f"%{description}%"))
    if min_mark is not None:
        query = query.where(book_table.c.avg_mark >= min_mark)
    if max_mark is not None:
        query = query.where(book_table.c.avg_mark <= max_mark)

    result = await session.execute(query)
    books = result.mappings().all()
    return [book['id'] for book in books]


async def get_book_from_db(session: AsyncSession, book_id: int):
    query = select(book_table).where(book_table.c.id == book_id)
    result = await session.execute(query)
    return result.mappings().first()


async def create_book_in_db(session: AsyncSession, book: BookCreate):
    book_dict = book.model_dump()
    if book_dict['genre']:
        genre_creation_model = GenreCreate(name=book_dict['genre'])
        genre_id = await get_existent_or_create_genre_in_db(session, genre_creation_model)
        book_dict['genre'] = genre_id

    author_creation_model = AuthorCreate(name=book_dict['author'])
    author_id = await get_existent_or_create_author_in_db(session, author_creation_model)
    book_dict['author'] = author_id

    query = insert(book_table).values(**book_dict)
    result = await session.execute(query)
    return result.inserted_primary_key[0]


async def update_book_in_db(session: AsyncSession, book_id: int, book: BookUpdate):
    book_in_db = await get_book_from_db(session, book_id)
    if book_in_db is None:
        return None

    book_dict = book.model_dump()
    if book_dict['pdf_qname'] and book_dict['pdf_qname'] != book_in_db['pdf_qname']:
        await delete_book(book_id)
        delete_file_in_s3(urllib.parse.unquote(book_in_db['pdf_qname']))
        await index_book(book_id, book_dict['genre'], book_dict['pdf_qname'])

    if book_dict['image_qname'] and book_dict['image_qname'] != book_in_db['image_qname']:
        await delete_book(book_id)
        delete_file_in_s3(urllib.parse.unquote(book_in_db['image_qname']))
        await index_book(book_id, book_dict['genre'], book_dict['image_qname'])

    if book_dict['genre']:
        genre_creation_model = GenreCreate(name=book_dict['genre'])
        genre_id = await get_existent_or_create_genre_in_db(session, genre_creation_model)
        book_dict['genre'] = genre_id

    if book_dict['author']:
        author_creation_model = AuthorCreate(name=book_dict['author'])
        author_id = await get_existent_or_create_author_in_db(session, author_creation_model)
        book_dict['author'] = author_id

    for key, value in book_dict.items():
        if book_dict[key] is None:
            book_dict[key] = book_in_db[key]

    query = update(book_table).where(book_table.c.id == book_id).values(**book_dict)
    await session.execute(query)
    return await get_book_from_db(session, book_id)


async def delete_book_from_db(session: AsyncSession, book_id: int):
    book = await get_book_from_db(session, book_id)
    if book:
        query = delete(book_table).where(book_table.c.id == book_id)
        await session.execute(query)
    return book
