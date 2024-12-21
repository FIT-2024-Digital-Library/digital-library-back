from .base import CamelCaseBaseModel

__all__ = ["Author", "AuthorCreate"]


class AuthorCreate(CamelCaseBaseModel):
    name: str

class Author(AuthorCreate):
    id: int
