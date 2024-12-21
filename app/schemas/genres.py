from .base import CamelCaseBaseModel

__all__ = ["Genre", "GenreCreate"]


class GenreCreate(CamelCaseBaseModel):
    name: str

class Genre(GenreCreate):
    id: int
