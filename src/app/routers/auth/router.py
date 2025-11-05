from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, status, Body, Request
from fastapi.security import (HTTPBearer,
                              OAuth2PasswordRequestForm)
from datetime import timedelta, datetime
import secrets
import string

from src.core.settings import settings_app
from src.core.database.orm import UserQuery
# from core.services.email_service import email_service

from src.app.configuration import (Server, get_password_hash,
                                       verify_password, is_email,
                                       create_access_token,
                                       verify_authorization)
from src.app.configuration.auth import create_refresh_token
from src.app.configuration.schemas import (
    UserResponse, UserLoginResponse, LoginRequest,
    Token,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest,
    TwoFactorEnableRequest, TwoFactorDisableRequest,
    EmailVerificationRequest, TwoFactorLoginRequest, PasswordResetResponse,
    TwoFactorStatusResponse, EmailVerificationResponse
)

import logging

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(http_bearer)])

logger = logging.getLogger("app.auth")


@router.post("/register/", response_model=Token)
async def register(user: UserLoginResponse = Body()):
    try:
        logger.info(f"Starting registration for user: {user.login}")
        
        logger.info("Checking if email exists...")
        db_user = await UserQuery.get_user_by_email(user.email)

        if db_user:
            logger.info("Email already exists")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        logger.info("Checking if login exists...")
        db_user = await UserQuery.get_user_by_login(user.login)

        if db_user:
            logger.info("Login already exists")
            raise HTTPException(status_code=400, detail="Login already registered")
        
        logger.info("Hashing password...")
        hashed_password = get_password_hash(user.password)

        logger.info("Creating user in database...")
        created_user = await UserQuery.create_user(
                                  name=user.name,
                                  login=user.login,
                                  password_hash=hashed_password,
                                  email=user.email)
        
        logger.info(f"User created with ID: {created_user.id}")
        
        logger.info("Creating access token...")
        access_token_expires = timedelta(minutes=settings_app.security.access_token_expire_minutes)
        access_token = create_access_token(payload={"sub": user.login, "email": user.email}, 
                                           expires_delta=access_token_expires)
        
        logger.info("Creating refresh token...")
        refresh_token = create_refresh_token(payload={"sub": user.login, "email": user.email})
        
        logger.info("Registration completed successfully")
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "message": "User registered successfully"
    }


@router.post("/login_user/", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
):
    
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get identifier from login, email, or username
    username = login_data.email or login_data.login or login_data.username
    password = login_data.password

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username/email and password are required"
        )

    identifier_type = "email" if is_email(username) else "login"
    
    if identifier_type == "email":
        user = await UserQuery.get_user_by_email(username)
    else:
        user = await UserQuery.get_user_by_login(username)

    if not user:
        raise unauthed_exc

    if not verify_password(password, user.password):
        raise unauthed_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings_app.security.access_token_expire_minutes)
    access_token = create_access_token(payload={"sub": user.login, "email": user.email}, 
                                        expires_delta=access_token_expires)
    refresh_token = create_refresh_token(payload={"sub": user.login, "email": user.email})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        message="User logged in successfully"
    )


@router.post("/refresh-token/", response_model=Token)
async def refresh_token_endpoint(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings_app.security.refresh_secret_key, algorithms=[settings_app.security.algorithm])
        token_type = payload.get("type")
        username: str = payload.get("sub")
        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    access_token_expires = timedelta(minutes=settings_app.security.access_token_expire_minutes)
    new_access_token = create_access_token(payload={"sub": username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(payload={"sub": username})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/user/me/", response_model=UserResponse)
async def auth_user_check_self_info(
    user: str = Depends(verify_authorization)
):
    return user


def _generate_token(length: int = 32) -> str:
    """Генерирует случайный токен"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _generate_verification_code() -> str:
    """Генерирует 6-значный код подтверждения"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


# @router.post("/password-reset-request/", response_model=PasswordResetResponse)
# async def request_password_reset(
#     request: PasswordResetRequest,
#     session: AsyncSession = Depends(Server.get_db)
# ):
#     """Запрос на сброс пароля"""
#     user = await UserQuery.get_user_by_email(UserLoginResponse(email=request.email, password=""))
    
#     if not user:
#         # Не раскрываем информацию о существовании email
#         return PasswordResetResponse(
#             message="Если email существует, на него будет отправлена инструкция по сбросу пароля",
#             success=True
#         )
    
#     # Генерируем токен для сброса пароля
#     reset_token = _generate_token()
#     expires_at = datetime.utcnow() + timedelta(hours=1)
    
#     await orm_set_password_reset_token(session, user.id, reset_token, expires_at)
    
#     # Отправляем email
#     email_sent = email_service.send_password_reset_email(
#         user.email, reset_token, user.login
#     )
    
#     if email_sent:
#         return PasswordResetResponse(
#             message="Инструкция по сбросу пароля отправлена на ваш email",
#             success=True
#         )
#     else:
#         raise HTTPException(
#             status_code=500,
#             detail="Ошибка отправки email"
#         )


# @router.post("/password-reset-confirm/", response_model=PasswordResetResponse)
# async def confirm_password_reset(
#     request: PasswordResetConfirm,
#     session: AsyncSession = Depends(Server.get_db)
# ):
#     """Подтверждение сброса пароля"""
#     user = await orm_get_user_by_reset_token(session, request.token)
    
#     if not user:
#         raise HTTPException(
#             status_code=400,
#             detail="Недействительный или истекший токен"
#         )
    
#     # Хешируем новый пароль
#     hashed_password = get_password_hash(request.new_password)
    
#     # Обновляем пароль и очищаем токен
#     await orm_update_user_password(session, user.id, hashed_password)
#     await orm_clear_password_reset_token(session, user.id)
    
#     return PasswordResetResponse(
#         message="Пароль успешно изменен",
#         success=True
#     )


@router.post("/change-password/", response_model=PasswordResetResponse)
async def change_password(
    request: ChangePasswordRequest,
    user: str = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Смена пароля авторизованным пользователем"""
    # Проверяем текущий пароль
    if not verify_password(request.current_password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Неверный текущий пароль"
        )
    
    # Хешируем новый пароль
    hashed_password = get_password_hash(request.new_password)
    
    # Обновляем пароль
    await UserQuery.update_user(user.id, name=user.name, login=user.login, email=user.email, password_hash=hashed_password)
    
    return PasswordResetResponse(
        message="Пароль успешно изменен",
        success=True
    )


@router.post("/two-factor/enable/", response_model=TwoFactorStatusResponse)
async def enable_two_factor(
    request: TwoFactorEnableRequest,
    user: str = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Включение двухфакторной аутентификации"""
    # Проверяем пароль
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Неверный пароль"
        )
    
    if not user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email должен быть подтвержден для включения 2FA"
        )
    
    # Генерируем секрет для 2FA
    secret = _generate_token(32)
    
    # Включаем 2FA
    # await orm_enable_two_factor(session, user.id, secret)
    
    return TwoFactorStatusResponse(
        enabled=True,
        email_verified=user.email_verified
    )


@router.post("/two-factor/disable/", response_model=TwoFactorStatusResponse)
async def disable_two_factor(
    request: TwoFactorDisableRequest,
    user: str = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Отключение двухфакторной аутентификации"""
    # Проверяем пароль
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Неверный пароль"
        )
    
    # Отключаем 2FA
    # await orm_disable_two_factor(session, user.id)
    
    return TwoFactorStatusResponse(
        enabled=False,
        email_verified=user.email_verified
    )


@router.get("/two-factor/status/", response_model=TwoFactorStatusResponse)
async def get_two_factor_status(
    user: str = Depends(verify_authorization)
):
    """Получение статуса двухфакторной аутентификации"""
    return TwoFactorStatusResponse(
        enabled=user.two_factor_enabled,
        email_verified=user.email_verified
    )


@router.post("/email-verification/", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    session: AsyncSession = Depends(Server.get_db)
):
    """Подтверждение email"""
    # user = await orm_get_user_by_verification_token(session, request.token)
    
    # if not user:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Недействительный токен подтверждения"
    #     )
    
    # # Подтверждаем email
    # await orm_verify_email(session, user.id)
    
    return EmailVerificationResponse(
        message="Email успешно подтвержден",
        success=True
    )


@router.post("/two-factor/login/", response_model=Token)
async def two_factor_login(
    request: TwoFactorLoginRequest,
    session: AsyncSession = Depends(Server.get_db)
):
    """Вход с двухфакторной аутентификацией"""
    # Здесь должна быть логика проверки кода 2FA
    # Для простоты пока возвращаем ошибку
    raise HTTPException(
        status_code=400,
        detail="Двухфакторная аутентификация пока не реализована полностью"
    )
