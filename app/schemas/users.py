from enum import Enum
from typing import Optional

from pydantic import Field, EmailStr
from .base import CamelCaseBaseModel

__all__ = ["User", "UserLogin", "UserRegister", "UserLogined"]


class PrivilegesEnum(str, Enum):
    BASIC = "basic"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserRegister(CamelCaseBaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")


class UserUpdate(CamelCaseBaseModel):
    password: Optional[str] = Field(default=None, min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
    name: Optional[str] = Field(default=None, min_length=3, max_length=50, description="Имя, от 3 до 50 символов")


class UserLogin(CamelCaseBaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")


class User(CamelCaseBaseModel):
    id: int
    email: EmailStr = Field(description="Электронная почта")
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    privileges: PrivilegesEnum


class UserLogined(CamelCaseBaseModel):
    email: EmailStr = Field(description="Электронная почта")
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    privileges: PrivilegesEnum
