# файл для query запросов
from datetime import datetime
from typing import List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from enum import Enum
from src.core.database.models import (News, NewsUrl, TelegramChannel)
from src.core.database import get_db_helper

class NewsType(Enum):
    
    telegram = "telegram"
    url = "url"
    rss = "RSS"
    api = "API"
    twitter = "TWITTER"

class NewsData(BaseModel):
    id_url: int
    title: str
    text: str
    type: NewsType
    date: datetime

class NewsQuery:


    @staticmethod
    async def add_news(news: NewsData) -> News:
        async with get_db_helper().get_session() as session:
            session.add(News(id_url=news.id_url, title=news.title, text=news.text, type=news.type, date=news.date))
            await session.commit()
            await session.refresh(news)
            return news

    @staticmethod
    async def get_telegram_channels(parsed: bool = None) -> List[TelegramChannel]:
        async with get_db_helper().get_session() as session:
            query = select(TelegramChannel)
            if parsed:
                query = query.where(TelegramChannel.parsed == parsed)
            result = await session.execute(query)
            return result.scalars().all()

    """Класс для работы с запросами к таблице telegram_channels"""
    @staticmethod
    async def add_telegram_channel(name: str, chat_id: str, parsed: bool = True) -> TelegramChannel:
        async with get_db_helper().get_session() as session:
            channel = await session.execute(select(TelegramChannel).where(TelegramChannel.name == name))
            if channel.scalars().first():
                raise ValueError(f"Channel {name} already exists")
            session.add(TelegramChannel(name=name, chat_id=chat_id, parsed=parsed))
            await session.commit()

    @staticmethod
    async def get_news_list(type: str = None, limit: int = 100, offset: int = 0) -> List[News]:
        async with get_db_helper().get_session() as session:
            query = select(News)
            if type:
                query = query.where(News.type == type)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_news_urls(parsed: bool = None) -> list[NewsUrl]:
        async with get_db_helper().get_session() as session:
            query = select(NewsUrl)

            if parsed:
                query = query.where(NewsUrl.parsed == parsed)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_news_url_by_id(url_id: int) -> NewsUrl:
        async with get_db_helper().get_session() as session:
            query = select(NewsUrl).where(NewsUrl.id == url_id)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def get_telegram_channel_by_id(channel_id: int) -> TelegramChannel:
        async with get_db_helper().get_session() as session:
            query = select(TelegramChannel).where(TelegramChannel.id == channel_id)
            result = await session.execute(query)
            return result.scalar()
