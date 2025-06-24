from sqlalchemy import MetaData, Table, Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import declarative_base


db_metadata = MetaData()
privileges_enum = ENUM("basic", "admin", "moderator", name="privileges", metadata=db_metadata)
Base = declarative_base()


class User(Base):
    __tablename__ = 'user_table'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    name = Column(String(30))
    password_hash = Column(String(512))
    privileges = Column(ENUM("basic", "admin", "moderator", name="privileges"), default="basic")


class Author(Base):
    __tablename__ = 'author_table'

    id = Column(Integer, primary_key=True)
    name = Column(String(150))


class Genre(Base):
    __tablename__ = 'genre_table'

    id = Column(Integer, primary_key=True)
    name = Column(String(150))


class Book(Base):
    __tablename__ = 'book_table'

    id = Column(Integer, primary_key=True)
    theme_id = Column(Integer, nullable=False)
    title = Column(String(50))
    author = Column(ForeignKey('author_table.id'), nullable=False)
    genre = Column(ForeignKey('genre_table.id'), nullable=True)
    published_date = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    image_qname = Column(String, nullable=True)
    pdf_qname = Column(String)
    avg_mark = Column(Float)
    marks_count = Column(Integer)


class Review(Base):
    __tablename__ = 'review_table'
    id = Column(Integer, primary_key=True)
    owner_id = Column(ForeignKey('user_table.id', ondelete='CASCADE'), index=True, nullable=False)
    book_id = Column(ForeignKey('book_table.id', ondelete='CASCADE'), index=True, nullable=False)
    mark = Column(Integer)
    text = Column(String, nullable=True)
    last_edit_date = Column(Date)
