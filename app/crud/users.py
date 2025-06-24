from abc import ABC, abstractmethod

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update, delete

from app.crud.crud_interface import CrudInterface
from app.models import User
from app.schemas import UserRegister, UserLogin, PrivilegesEnum, UserUpdate, UserLogined
from app.utils import get_password_hash, verify_password


class UsersCrud(CrudInterface):
    @classmethod
    async def get(cls, connection: AsyncConnection, element_id: int):
        query = select(
            User.id,
            User.email,
            User.name,
            User.privileges
        ).where(User.id == element_id)
        result = await connection.execute(query)
        return result.mappings().first()

    @classmethod
    async def get_multiple(cls, connection: AsyncConnection, username=None, email=None):
        query = select(
            User.id,
            User.email,
            User.name,
            User.privileges
        )
        if username:
            query = query.where(User.name.ilike(f"%{username}%"))
        if email:
            query = query.where(User.email.ilike(f"%{email}%"))

        result = await connection.execute(query)
        return result.mappings().all()

    @classmethod
    async def create(cls, connection: AsyncConnection, model: UserRegister):
        query = select(User).where(User.email == model.email)
        result = await connection.execute(query)
        result = result.first()
        if result:
            raise HTTPException(status_code=409, detail="User already exists")

        user_dict = model.model_dump()
        user_dict["password_hash"] = get_password_hash(model.password)
        user_dict['privileges'] = "basic"
        user_dict.pop("password")

        stmt = insert(User).values(**user_dict).returning(User.id)
        result = await connection.execute(stmt)
        user_id = result.scalar_one()

        if user_id == 1:
            await cls.set_role_for_user(connection, PrivilegesEnum.ADMIN, 1)
            user_dict['privileges'] = "admin"

        user_dict.pop("password_hash")
        return user_dict

    @classmethod
    async def delete(cls, connection: AsyncConnection, element_id: int):
        user = await cls.get(connection, element_id)
        if user:
            query = delete(User).where(User.id == element_id)
            await connection.execute(query)
        return user

    @classmethod
    async def update(cls, connection: AsyncConnection, element_id: int, model: UserUpdate):
        user_current_data = await cls.get(connection, element_id)
        if user_current_data is None:
            raise HTTPException(status_code=403, detail="User doesn't exist")

        user_new_dict = model.model_dump()

        for key, value in user_current_data.items():
            if key not in user_new_dict.keys() or user_new_dict[key] is None:
                user_new_dict[key] = value

        if model.password is not None:
            user_new_dict["password_hash"] = get_password_hash(model.password)
        user_new_dict.pop("password")

        query = update(User).where(User.id == element_id).values(**user_new_dict)
        await connection.execute(query)

        user = await cls.get(connection, element_id)
        return user

    @classmethod
    async def set_role_for_user(cls, connection: AsyncConnection, privilege: PrivilegesEnum, user_id: int):
        user = await cls.get(connection, user_id)
        if user is None:
            raise HTTPException(status_code=403, detail="User doesn't exist")

        query = update(User).where(User.id == user_id).values(privileges=privilege)
        await connection.execute(query)
        return await cls.get(connection, user_id)

    @classmethod
    async def login(cls, connection: AsyncConnection, user_data: UserLogin):
        query = select(User).where(User.email == user_data.email)
        result = await connection.execute(query)
        print(result.keys())
        user = result.mappings().first()
        if not user or not verify_password(user_data.password, user["password_hash"]):
            return None
        return user
