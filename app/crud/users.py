from fastapi import HTTPException
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import user_table
from app.schemas import UserRegister, UserLogin
from app.schemas.users import PrivilegesEnum, UserUpdate, UserLogined
from app.utils import get_password_hash, verify_password


async def register_user(session: AsyncSession, user_data: UserRegister):
    query = select(user_table).where(user_table.c.email == user_data.email)
    result = await session.execute(query)
    result = result.first()
    if result:
        raise HTTPException(status_code=409, detail="User already exists")
    user_dict = user_data.model_dump()

    user_dict["password_hash"] = get_password_hash(user_data.password)
    user_dict['privileges'] = "basic"
    user_dict.pop("password")
    query = insert(user_table).values(**user_dict)
    result = await session.execute(query)
    key = result.inserted_primary_key
    if key:
        if key == 1:
            await set_role_for_user(session, PrivilegesEnum.ADMIN, 1)
        user_dict.pop("password_hash")
        return user_dict


async def login_user(session: AsyncSession, user_data: UserLogin):
    query = select(user_table).where(
        user_table.c.email == user_data.email)
    result = await session.execute(query)
    user = result.mappings().first()
    if not user or verify_password(plain_password=user_data.password,
                                   hashed_password=user["password_hash"]) is False:
        return None
    return user


async def find_user_by_id(session: AsyncSession, user_id: int):
    query = select(
        user_table.c.id,
        user_table.c.email,
        user_table.c.name,
        user_table.c.privileges
    ).where(user_table.c.id == user_id)

    result = await session.execute(query)
    user = result.mappings().first()
    return user


async def get_users_from_db(session: AsyncSession):
    query = select(
        user_table.c.id,
        user_table.c.email,
        user_table.c.name,
        user_table.c.privileges
    )

    result = await session.execute(query)
    user = result.mappings().all()
    return user


async def delete_user_from_db(session: AsyncSession, user_id: int):
    user = await find_user_by_id(session, user_id)
    if user:
        query = delete(user_table).where(user_table.c.id == user_id)
        await session.execute(query)
    return user


async def update_user_in_db(session: AsyncSession, user_id: int, user_new_data: UserUpdate):
    user_current_data = await find_user_by_id(session, user_id)
    if user_current_data is None:
        raise HTTPException(status_code=403, detail="User doesn't exist")

    user_new_dict = user_new_data.model_dump()

    for key, value in user_current_data.items():
        if key not in user_new_dict.keys() or user_new_dict[key] is None:
            user_new_dict[key] = value
    if user_new_data.password is not None:
        user_new_dict["password_hash"] = get_password_hash(user_new_data.password)
    user_new_dict.pop("password")
    print(user_new_dict)
    query = update(user_table).where(user_table.c.id == user_id).values(**user_new_dict)
    await session.execute(query)

    user = await find_user_by_id(session, user_id)
    return user


async def set_role_for_user(session: AsyncSession, privilege: PrivilegesEnum, user_id: int):
    user = await find_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=403, detail="User doesn't exist")

    query = update(user_table).where(user_table.c.id == user_id).values(**{'privileges': privilege})
    await session.execute(query)
    user = await find_user_by_id(session, user_id)
    return user
