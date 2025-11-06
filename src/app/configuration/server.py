import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from passlib.context import CryptContext
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from .routers import Routers
from src.core.settings import settings_app
from src.core.database import get_db_helper  # only for type; do not rely on this binding at runtime
from .middleware.observability import ObservabilityMiddleware

class Server:

    __app: FastAPI

    # Legacy Jinja templates removed; frontend is served by Vite React app
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    http_bearer = HTTPBearer(auto_error=False)
    # Must point to the OAuth2 password flow token endpoint, not a secret key
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login_user/")
    frontend_url = settings_app.app.frontend_url

    def __init__(self, app: FastAPI):

        self.__app = app
        self.__register_routers(app)
        self.__regist_middleware(app)
        self.__register_static_files(app)

    @staticmethod
    def __register_static_files(app: FastAPI):
        static_dir = Path(__file__).parent.parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @staticmethod
    def get_static_file():
        static_dir = Path(__file__).parent.parent / "static"
        if static_dir.exists():
            with open(static_dir / "index.html", "r", encoding="utf-8") as f:
                return f.read()
        return None
        
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
        
        # Get allowed origins based on environment
        allowed_origins = settings_app.app.get_allowed_origins(debug=settings_app.debug)
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

