from datetime import date
from typing import Optional
from .base import CamelCaseBaseModel

__all__ = ["Book", "BookCreate", "BookUpdate"]


class BookCreate(CamelCaseBaseModel):
    theme_id: int
    title: str
    author: str
    genre: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_qname: Optional[str] = None
    pdf_qname: str

class BookUpdate(BookCreate):
    pass

class Book(BookCreate):
    id: int
