from datetime import date
from typing import Optional
from .base import CamelCaseBaseModel

__all__ = ["Book", "BookCreate"]


class Book(CamelCaseBaseModel):
    id: int
    theme_id: int
    title: str
    author: int
    genre: Optional[int] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    pdf_url: str


class BookCreate(CamelCaseBaseModel):
    theme_id: int
    title: str
    author: str
    genre: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    pdf_url: str


class BookUpdate(CamelCaseBaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None
