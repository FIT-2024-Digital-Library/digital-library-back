from fastapi import APIRouter, HTTPException, status, Response, Depends

from app.schemas import UserRegister, UserLogin, User, UserLogined, PrivilegesEnum, UserUpdate
from app.services import UserService
from app.utils import UnitOfWork, get_uow
from app.utils.auth import get_current_user, user_has_permissions


router = APIRouter(
    prefix='/users',
    tags=['user']
)


@router.get('/profile', response_model=User, summary='Returns authorized user')
async def get_profile(user_data: User = Depends(get_current_user)):
    return user_data


@router.post('/login', response_model=User, summary='Logs user in')
async def login(response: Response, user_data: UserLogin, uow: UnitOfWork = Depends(get_uow)):
    return await UserService.login(response, user_data, uow)


@router.post('/register', response_model=UserLogined, summary='Creates new user')
async def register(user_data: UserRegister, uow: UnitOfWork = Depends(get_uow)):
    return await UserService.register(user_data, uow)


@router.post("/logout", response_model=None, summary='Log out of system')
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token", secure=True, samesite='none')
    return {'message': 'You successfully logged out'}


@router.post('/{user_id}/set_privilege', response_model=User, summary='Sets the privilege for user')
async def set_privilege_for_user(
        user_id: int, privilege: PrivilegesEnum,
        user_creds: User = user_has_permissions(PrivilegesEnum.ADMIN),
        uow: UnitOfWork = Depends(get_uow)
):
    return await UserService.set_privilege_for_user(user_id, privilege, uow)


@router.put('/{user_id}/update', response_model=User, summary='Updates user by id')
async def update_user_by_id(
        user_id: int,
        user_data: UserUpdate,
        user_creds: User = Depends(get_current_user),
        uow: UnitOfWork = Depends(get_uow)
):
    return await UserService.update_user_by_id(user_id, user_data, user_creds, uow)


@router.delete('/{user_id}/delete', response_model=User, summary='Deletes user by id')
async def delete_user_by_id(
        user_id: int, user_creds: User = Depends(get_current_user), uow: UnitOfWork = Depends(get_uow)
):
    return await UserService.delete_user_by_id(user_id, user_creds, uow)


@router.get('/{user_id}', response_model=User, summary='Returns user by id')
async def get_user_by_id(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    return await UserService.get_user_by_id(user_id, uow)


@router.get('/', response_model=list[User], summary='Returns all users')
async def get_users(
        user_creds: User = user_has_permissions(PrivilegesEnum.ADMIN), uow: UnitOfWork = Depends(get_uow)
):
    return await UserService.get_users(uow)
