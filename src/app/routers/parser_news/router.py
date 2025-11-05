from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.app.configuration import Server
from src.app.configuration.schemas import NewsResponse, TelegramChannelResponse, NewsUrlResponse
from src.core.database.orm import NewsQuery

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/", response_model=List[NewsResponse])
async def get_news(
    type: Optional[str] = Query(None, description="Тип новости"),
    limit: int = Query(100, description="Максимальное количество новостей"),
    offset: int = Query(0, description="Смещение для пагинации"),
):
    """
    Получить список новостей с фильтрами
    """
    news_list = await NewsQuery.get_news_list(type=type, limit=limit, offset=offset)
    return news_list


@router.get("/urls", response_model=List[NewsUrlResponse])
async def get_news_urls(
    parsed: Optional[bool] = Query(None, description="Фильтр по статусу парсинга")):
    """
    Получить список URL новостей
    """
    urls = await NewsQuery.get_news_urls(parsed=parsed)
    return urls


@router.get("/urls/{url_id}", response_model=NewsUrlResponse)
async def get_news_url_by_id(
    url_id: int):
    """
    Получить информацию о URL новости по ID
    """
    news_url = await NewsQuery.get_news_url_by_id(url_id)
    
    if not news_url:
        raise HTTPException(status_code=404, detail=f"News URL {url_id} not found")
    
    return news_url


@router.get("/channels", response_model=List[TelegramChannelResponse])
async def get_telegram_channels(
    parsed: Optional[bool] = Query(None, description="Фильтр по статусу парсинга"),):
    """
    Получить список Telegram каналов
    """
    channels = await NewsQuery.get_telegram_channels(parsed=parsed)
    return channels


@router.get("/channels/{channel_id}", response_model=TelegramChannelResponse)
async def get_telegram_channel_by_id(
    channel_id: int):
    """
    Получить информацию о Telegram канале по ID
    """
    channel = await NewsQuery.get_telegram_channel_by_id(channel_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail=f"Telegram channel {channel_id} not found")
    
    return channel

