from fastapi import APIRouter, HTTPException, status, Response, Depends

from app.repositories.users import UsersCrud
from app.models import Base
from app.schemas import UserRegister, UserLogin, User, UserLogined, PrivilegesEnum, UserUpdate
from app.utils.auth import create_access_token, get_current_user, user_has_permissions
from app.utils.unit_of_work import UnitOfWork, get_uow

router = APIRouter(
    prefix='/users',
    tags=['user']
)


@router.get('/profile', response_model=User, summary='Returns authorized user')
async def get_profile(user_data: User = Depends(get_current_user)):
    return user_data


@router.post('/login', response_model=User, summary='Logs user in')
async def login(response: Response, user_data: UserLogin, uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        user = await UsersCrud.login(uow.get_connection(), user_data)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Wrong password or email')
        access_token = create_access_token({"sub": str(user.id)})
        response.set_cookie(key="users_access_token", value=access_token, httponly=True, secure=True, samesite='none')
        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "privileges": user.privileges
        }
        return user_data


@router.post('/register', response_model=UserLogined, summary='Creates new user')
async def register(user_data: UserRegister, uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        data = await UsersCrud.create(uow.get_connection(), user_data)
        return data


@router.post("/logout", response_model=None, summary='Log out of system')
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token", secure=True, samesite='none')
    return {'message': 'You successfully logged out'}


@router.post('/{user_id}/set_privilege', response_model=User, summary='Sets the privilege for user')
async def set_privilege_for_user(user_id: int, privilege: PrivilegesEnum,
                                 user_creds: User = user_has_permissions(PrivilegesEnum.ADMIN),
                                 uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        data = await UsersCrud.set_role_for_user(uow.get_connection(), privilege, user_id)
        return data


@router.put('/{user_id}/update', response_model=User, summary='Updates user by id')
async def update_user_by_id(user_id: int, user_data: UserUpdate,
                            user_creds: User = Depends(get_current_user), uow: UnitOfWork = Depends(get_uow)):
    if user_creds.privileges == PrivilegesEnum.ADMIN or user_creds.id == user_id:
        async with uow.begin():
            data = await UsersCrud.update(uow.get_connection(), user_id, user_data)
            return data
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')


@router.delete('/{user_id}/delete', response_model=User, summary='Deletes user by id')
async def delete_user_by_id(user_id: int,
                            user_creds: User = Depends(get_current_user), uow: UnitOfWork = Depends(get_uow)):
    if user_creds.privileges == PrivilegesEnum.ADMIN or user_creds.id == user_id:
        async with uow.begin():
            data = await UsersCrud.delete(uow.get_connection(), user_id)
            if data is None:
                raise HTTPException(status_code=403, detail="User doesn't exist")
            return data
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')


@router.get('/{user_id}', response_model=User, summary='Returns user by id')
async def get_user_by_id(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        user = await UsersCrud.get(uow.get_connection(), user_id)
        if user is None:
            raise HTTPException(status_code=403, detail="User doesn't exist")
        return user


@router.get('/', response_model=list[User], summary='Returns all users')
async def get_users(user_creds: User = user_has_permissions(PrivilegesEnum.ADMIN), uow: UnitOfWork = Depends(get_uow)):
    async with uow.begin():
        data = await UsersCrud.get_multiple(uow.get_connection())
        return data
