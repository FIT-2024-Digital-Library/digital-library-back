from sqlalchemy import MetaData, Table, Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.dialects.postgresql import ENUM

db_metadata = MetaData()

privileges_enum = ENUM("basic", "admin", "moderator", name="privileges", metadata=db_metadata)

user_table = Table(
    "user_table",
    db_metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String),
    Column("name", String(30)),
    Column("password_hash", String(512)),
    Column("privileges", privileges_enum, default="basic")  # TODO: по хорошему надо будет заменить на группы
)

author_table = Table(
    "author_table",
    db_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(150))
)

genre_table = Table(
    "genre_table",
    db_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(150))
)

book_table = Table(
    "book_table",
    db_metadata,
    Column("id", Integer, primary_key=True),
    Column("theme_id", Integer, nullable=False),
    Column("title", String(50)),
    Column("author", ForeignKey(author_table.c.id), nullable=False),
    Column("genre", ForeignKey(genre_table.c.id), nullable=True),
    Column("published_date", Integer, nullable=True),
    Column("description", String, nullable=True),
    Column("image_qname", String, nullable=True),
    Column("pdf_qname", String),
    Column("avg_mark", Float),
    Column("marks_count", Integer)
)

review_table = Table(
    "review_table",
    db_metadata,
    Column("id", Integer, primary_key=True),
    Column("owner_id", ForeignKey(user_table.c.id, ondelete='CASCADE'), index=True, nullable=False),
    Column("book_id", ForeignKey(book_table.c.id, ondelete='CASCADE'), index=True, nullable=False),
    Column("mark", Integer),
    Column("text", String, nullable=True),
    Column("last_edit_date", Date)
)
