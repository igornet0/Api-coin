import asyncio
from typing import Optional, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends, status, Form
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import re

from src.core.settings import settings_app
from src.core.database.models import User
from src.core.database.orm import UserQuery

from .schemas import TokenData, UserLoginResponse
from .server import Server

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def is_email(string: str) -> bool:
    """Проверяет, соответствует ли строка формату email"""
    return re.fullmatch(EMAIL_REGEX, string) is not None

def verify_password(plain_password, hashed_password) -> bool:
    """Verify password against bcrypt hash; fallback to legacy SHA-256 hex.

    This keeps compatibility with admins created by direct scripts that stored
    SHA-256 hex digests instead of bcrypt. """
    try:
        import bcrypt
        # Use bcrypt directly to avoid passlib issues
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        pass
    try:
        import hashlib
        legacy_sha256 = hashlib.sha256(plain_password.encode()).hexdigest()
        return legacy_sha256 == hashed_password
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    import bcrypt
    # Bcrypt has a 72 character limit, truncate if necessary
    if len(password) > 72:
        password = password[:72]
    
    # Use bcrypt directly to avoid passlib issues
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(payload: dict,
                        secret_key: str = settings_app.security.secret_key,
                        algorithm: str = settings_app.security.algorithm,
                        expires_delta: Optional[timedelta] = None):
    to_encode = payload.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings_app.security.access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), TOKEN_TYPE_FIELD: ACCESS_TOKEN_TYPE})

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

def decode_access_token(token: str | bytes, secret_key: str = None,
                        algorithm: str = settings_app.security.algorithm):
    if secret_key is None:
        secret_key = settings_app.security.secret_key
    
    return jwt.decode(token, secret_key, algorithms=[algorithm])

def create_refresh_token(payload: dict,
                         secret_key: str = settings_app.security.refresh_secret_key,
                         algorithm: str = settings_app.security.refresh_algorithm,
                         expires_delta: Optional[timedelta] = None):
    to_encode = payload.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings_app.security.refresh_token_expire_days)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), TOKEN_TYPE_FIELD: REFRESH_TOKEN_TYPE})

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

def decode_refresh_token(token: str | bytes,
                         secret_key: str = settings_app.security.refresh_secret_key,
                         algorithm: str = settings_app.security.refresh_algorithm):
    return jwt.decode(token, secret_key, algorithms=[algorithm])

def get_current_token_payload(
    token: str = Depends(Server.oauth2_scheme),
) -> dict:
    try:
        payload = decode_access_token(
            token=token,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
        )
    
    return payload

def validate_token_type(
    payload: dict,
    token_type: str,
) -> bool:
    
    current_token_type = payload.get(TOKEN_TYPE_FIELD)

    if current_token_type == token_type:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"invalid token type {current_token_type!r} expected {token_type!r}",
    )

async def get_user_by_token_sub(payload: dict, session: Annotated[AsyncSession, Depends(Server.get_db)]) -> User:

    username: str | None = payload.get("sub")

    if username:
        
        user = await UserQuery.get_user_by_login(username)

        if user:
            return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )

def get_auth_user_from_token_of_type(token_type: str):
    async def get_auth_user_from_token(
        payload: dict = Depends(get_current_token_payload),
        session: AsyncSession = Depends(Server.get_db),
    ) -> User:

        validate_token_type(payload, token_type)
        
        return await get_user_by_token_sub(payload, session)

    return get_auth_user_from_token

def get_current_active_auth_user(
    current_user,
):
    if current_user.is_active:
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="inactive user",
    )

async def validate_auth_user(
        response: UserLoginResponse,
        session: AsyncSession = Depends(Server.get_db),
    ):

    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await UserQuery.get_user_by_login(response)

    if not user:
        raise unauthed_exc

    if not verify_password(
        plain_password=response.password,
        hashed_password=user.password,
    ):
        raise unauthed_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user inactive",
        )

    return user

async def get_current_user(token: Annotated[str, Depends(Server.oauth2_scheme)], db: Annotated[AsyncSession, Depends(Server.get_db)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)

        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
        
        token_data = TokenData(login=username)

    except JWTError:
        raise credentials_exception
    
    user = await UserQuery.get_user_by_login(token_data)

    if user is None:
        raise credentials_exception
    
    return user

async def verify_authorization(token: str = Depends(Server.oauth2_scheme), 
                               session: AsyncSession = Depends(Server.get_db)):
    
    payload = get_current_token_payload(token)
    validate_token_type(payload, "access")

    user = await get_user_by_token_sub(payload, session)
    
    if user.is_active:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="inactive user",
    )

async def verify_authorization_admin(token: str = Depends(Server.oauth2_scheme), 
                               session: AsyncSession = Depends(Server.get_db)):
    
    payload = get_current_token_payload(token)
    validate_token_type(payload, "access")

    user = await get_user_by_token_sub(payload, session)
    
    if user.is_active and user.role == "admin":
        return user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="inactive user",
    )