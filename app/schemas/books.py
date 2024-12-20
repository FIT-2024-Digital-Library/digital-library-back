from datetime import date
from typing import Optional
from .base import CamelCaseBaseModel

__all__ = ["Book", "BookCreate", "BookUpdate"]


class Book(CamelCaseBaseModel):
    id: int
    theme_id: int
    title: str
    author: int
    genre: Optional[int] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_qname: Optional[str] = None
    pdf_qname: str


class BookCreate(CamelCaseBaseModel):
    theme_id: int
    title: str
    author: str
    genre: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_qname: Optional[str] = None
    pdf_qname: str


class BookUpdate(CamelCaseBaseModel):
    theme_id: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    image_qname: Optional[str] = None
    pdf_qname: Optional[str] = None
