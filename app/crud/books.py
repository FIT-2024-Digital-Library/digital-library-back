import urllib.parse
from datetime import date
from sqlalchemy import and_, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.authors import AuthorsCrud
from app.crud.crud_interface import CrudInterface
from app.crud.genres import GenresCrud
from app.crud.indexing import Indexing
from app.crud.storage import Storage
from app.models import book_table, author_table, genre_table
from app.schemas import BookCreate, GenreCreate, AuthorCreate
from app.schemas.books import BookUpdate


class BooksCrud(CrudInterface):
    @classmethod
    async def get(cls, session: AsyncSession, element_id: int):
        query = select(book_table, author_table.c.name.label('author_str')) \
            .where(and_(book_table.c.id == element_id, book_table.c.author == author_table.c.id))
        result = await session.execute(query)
        book_dict = dict(result.mappings().first())
        book_dict['author'] = book_dict['author_str']
        if book_dict['genre']:
            query = select(genre_table.c.name) \
                .where(genre_table.c.id == book_dict['genre'])
            result = await session.execute(query)
            book_dict['genre'] = result.scalar()
        return book_dict

    @classmethod
    async def get_multiple(cls, session: AsyncSession, title=None, author=None, genre=None, published_date=None,
                           description=None, min_mark=None, max_mark=None):
        query = select(book_table.c.id)
        if title:
            query = query.where(book_table.c.title.ilike(f"%{title}%"))
        if author:
            author_in_db = await AuthorsCrud.get_multiple(session, author)
            if not author_in_db:
                return []
            author_id = author_in_db[0].get("id")
            query = query.where(book_table.c.author == author_id)
        if genre:
            genre_in_db = await GenresCrud.get_multiple(session, genre)
            if not genre_in_db:
                return []
            genre_id = genre_in_db[0].get("id")
            query = query.where(book_table.c.genre == genre_id)
        if published_date:
            query = query.where(book_table.c.published_date == published_date)
        if description:
            query = query.where(book_table.c.description.ilike(f"%{description}%"))
        if min_mark:
            query = query.where(book_table.c.avg_mark >= min_mark)
        if max_mark:
            query = query.where(book_table.c.avg_mark <= max_mark)

        result = await session.execute(query)
        books = result.mappings().all()
        return [book['id'] for book in books]

    @classmethod
    async def create(cls, session: AsyncSession, model: BookCreate):
        book_dict = model.model_dump()
        if book_dict['genre']:
            genre_creation_model = GenreCreate(name=book_dict['genre'])
            genre_id = await GenresCrud.get_existent_or_create(session, genre_creation_model)
            book_dict['genre'] = genre_id

        author_creation_model = AuthorCreate(name=book_dict['author'])
        author_id = await AuthorsCrud.get_existent_or_create(session, author_creation_model)
        book_dict['author'] = author_id

        query = insert(book_table).values(**book_dict)
        result = await session.execute(query)
        return await cls.get(session, result.inserted_primary_key[0])

    @classmethod
    async def delete(cls, session: AsyncSession, element_id: int):
        book = await cls.get(session, element_id)
        if book:
            query = delete(book_table).where(book_table.c.id == element_id)
            await session.execute(query)
        return book

    @classmethod
    async def update(cls, session: AsyncSession, element_id: int, model: BookUpdate):
        query = select(book_table).where(and_(book_table.c.id == element_id, book_table.c.author == author_table.c.id))
        result = await session.execute(query)
        book_in_db = dict(result.mappings().first())

        if not book_in_db:
            return None

        book_dict = model.model_dump()

        if book_dict['pdf_qname'] and book_dict['pdf_qname'] != book_in_db['pdf_qname']:
            await Indexing.delete_book(element_id)
            Storage.delete_file_in_s3(urllib.parse.unquote(book_in_db['pdf_qname']))
            await Indexing.index_book(element_id, book_dict['genre'], urllib.parse.unquote(book_dict['pdf_qname']))

        if book_dict['image_qname'] and book_dict['image_qname'] != "" and book_dict['image_qname'] != book_in_db[
            'image_qname'] and book_in_db['image_qname'] and book_in_db['image_qname'] != "":
            Storage.delete_file_in_s3(urllib.parse.unquote(book_in_db['image_qname']))

        if book_dict['genre']:
            genre_creation_model = GenreCreate(name=book_dict['genre'])
            genre_id = await GenresCrud.get_existent_or_create(session, genre_creation_model)
            book_dict['genre'] = genre_id

        if book_dict['author']:
            author_creation_model = AuthorCreate(name=book_dict['author'])
            author_id = await AuthorsCrud.get_existent_or_create(session, author_creation_model)
            book_dict['author'] = author_id

        for key, value in book_in_db.items():
            if key not in book_dict or book_dict[key] is None:
                book_dict[key] = value
        query = update(book_table).where(book_table.c.id == element_id).values(**book_dict)
        await session.execute(query)
        return await cls.get(session, element_id)
