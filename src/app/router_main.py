from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse

from .configuration import Server

import logging

router = APIRouter(tags=["Main"])

logger = logging.getLogger("app_fastapi.main")

# @router.get("/")
# async def read_root(request: Request):
#     return RedirectResponse(url=f"{Server.frontend_url}/")

# @router.get("/health")
# async def health_check():
#     return {"status": "ok"}


@router.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Главная страница с фронтендом
    """
    static_file = Server.get_static_file()
    if static_file:
        return static_file
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)

@router.get("/trade", response_class=HTMLResponse)
async def read_root_trade():
    """
    Главная страница с фронтендом
    """
    return RedirectResponse(url=f"{Server.frontend_url}/")

@router.get("/api")
async def api_info():
    """
    Информация об API
    """
    return {
        "message": "KuCoin Parser API",
        "version": "1.0.0",
        "endpoints": {
            "coins": "/coins",
            "news": "/news",
            "parsing": "/parsing"
        },
        "docs": "/docs"
    }


@router.get("/health")
async def health_check():
    """
    Проверка здоровья приложения
    """
    return {"status": "healthy"}

