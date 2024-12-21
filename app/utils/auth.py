from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, status, Depends

from app.crud.users import find_user_by_id
from app.schemas import User
from app.schemas.users import PrivilegesEnum
from app.settings import auth_cred, async_session_maker

__all__ = ["create_access_token", "get_current_user", "user_has_permissions"]
_priority_ = {
    "basic": 1,
    "moderator": 2,
    "admin": 3,
}


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, auth_cred.secret_key, algorithm=auth_cred.algorithm)
    return encode_jwt


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, auth_cred.secret_key, algorithms=[auth_cred.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token is invalid')

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User author_id wasn\'t found')
    async with async_session_maker() as session:
        user = await find_user_by_id(session, int(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


def user_has_permissions(permission: PrivilegesEnum):
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        if _priority_[current_user.privileges] >= _priority_[permission]:
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')

    return Depends(check_permission)
