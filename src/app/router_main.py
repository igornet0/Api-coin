from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from .configuration import Server

import logging

router = APIRouter(tags=["Main"])

logger = logging.getLogger("app_fastapi.main")

@router.get("/")
async def read_root(request: Request):
    return RedirectResponse(url=f"{Server.frontend_url}/")

@router.get("/health")
async def health_check():
    return {"status": "ok"}