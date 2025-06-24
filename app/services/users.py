from fastapi import HTTPException, status, Response

from app.repositories import UsersRepository
from app.schemas import PrivilegesEnum, UserRegister, UserLogin, User, UserLogined, UserUpdate
from app.utils import UnitOfWork
from app.utils.auth import create_access_token


__all__ = ["UserService"]


class UserService:
    @staticmethod
    async def login(response: Response, user_data: UserLogin, uow: UnitOfWork) -> User:
        async with uow.begin():
            user = await UsersRepository.login(uow.get_connection(), user_data)
            if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password or email")
            access_token = create_access_token({"sub": str(user.id)})
            response.set_cookie(
                key="users_access_token", value=access_token, httponly=True, secure=True, samesite='none'
            )
            return User(**user.model_dump())

    @staticmethod
    async def register(user_data: UserRegister, uow: UnitOfWork) -> UserLogined:
        async with uow.begin():
            data = await UsersRepository.create(uow.get_connection(), user_data)
            return data

    @staticmethod
    async def set_privilege_for_user(
            user_id: int, privilege: PrivilegesEnum, uow: UnitOfWork
    ) -> User:
        async with uow.begin():
            data = await UsersRepository.set_role_for_user(uow.get_connection(), privilege, user_id)
            return data

    @staticmethod
    async def update_user_by_id(
            user_id: int, user_data: UserUpdate, user_creds: User, uow: UnitOfWork
    ) -> User:
        if user_creds.privileges == PrivilegesEnum.ADMIN or user_creds.id == user_id:
            async with uow.begin():
                data = await UsersRepository.update(uow.get_connection(), user_id, user_data)
                return data
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')

    @staticmethod
    async def delete_user_by_id(user_id: int, user_creds: User, uow: UnitOfWork) -> User:
        if user_creds.privileges == PrivilegesEnum.ADMIN or user_creds.id == user_id:
            async with uow.begin():
                data = await UsersRepository.delete(uow.get_connection(), user_id)
                if data is None:
                    raise HTTPException(status_code=403, detail="User doesn't exist")
                return data
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')

    @staticmethod
    async def get_user_by_id(user_id: int, uow: UnitOfWork) -> User:
        async with uow.begin():
            user = await UsersRepository.get(uow.get_connection(), user_id)
            if user is None:
                raise HTTPException(status_code=403, detail="User doesn't exist")
            return user

    @staticmethod
    async def get_users(uow: UnitOfWork) -> list[User]:
        async with uow.begin():
            data = await UsersRepository.get_multiple(uow.get_connection())
            return data
