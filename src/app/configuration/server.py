import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from .routers import Routers
from core.settings import get_settings
from core.database import get_db_helper  # only for type; do not rely on this binding at runtime
from .lifespan import lifespan
from .middleware.observability import ObservabilityMiddleware

settings = get_settings()

class Server:

    __app: FastAPI

    # Legacy Jinja templates removed; frontend is served by Vite React app
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    http_bearer = HTTPBearer(auto_error=False)
    # Must point to the OAuth2 password flow token endpoint, not a secret key
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login_user/")
    frontend_url = settings.app.frontend_url
    lifespan = lifespan

    def __init__(self, app: FastAPI):

        self.__app = app
        self.__app.lifespan = lifespan
        self.__register_routers(app)
        self.__regist_middleware(app)

    @staticmethod
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with get_db_helper().get_session() as session:
            yield session

    def get_app(self) -> FastAPI:
        return self.__app

    @staticmethod
    def __register_routers(app: FastAPI):

        Routers(Routers._discover_routers()).register(app)

    @staticmethod
    def __regist_middleware(app: FastAPI):
        app.add_middleware(ObservabilityMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.app.allowed_origins_urls,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

