from enum import Enum
from typing import Optional

from pydantic import Field, EmailStr
from .base import CamelCaseBaseModel

__all__ = ["User", "UserLogin", "UserRegister", "UserLogined", "PrivilegesEnum", "UserUpdate"]


class PrivilegesEnum(str, Enum):
    BASIC = "basic"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserUpdate(CamelCaseBaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    password: Optional[str] = Field(default=None, min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")


class UserLogin(CamelCaseBaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")


class UserRegister(UserLogin):
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")


class UserLogined(CamelCaseBaseModel):
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    email: EmailStr = Field(description="Электронная почта")
    privileges: PrivilegesEnum


class User(UserLogined):
    id: int
