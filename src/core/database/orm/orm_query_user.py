# файл для query запросов
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from src.core.database.models import (User, KucoinApiKey)
from src.core.database import get_db_helper

class UserQuery:
    """Класс для работы с запросами к базе данных users"""

    @staticmethod
    async def create_user(name: str, login: str, email: str, password_hash: str) -> User:
        """Создать user
        Args:
            name: str - имя пользователя
            login: str - login пользователя
            email: str - email пользователя
            password_hash: str - хеш пароля
        Returns:
            User
        """
        async with get_db_helper().get_session() as session:
            user = User(name=name, login=login, email=email, password=password_hash)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def update_user(user_id: int, name: str, login: str, email: str, password_hash: str) -> User:
        """Обновить user
        Args:
            user_id: int - id пользователя
            name: str - имя пользователя
            login: str - login пользователя
            email: str - email пользователя
            password_hash: str - хеш пароля
        Returns:
            User
        """
        async with get_db_helper().get_session() as session:
            user = await UserQuery.get_user_by_id(user_id)
            user.name = name
            user.login = login
            user.email = email
            user.password_hash = password_hash
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        """Получить user по id
        Args:
            user_id: int - id пользователя
        Returns:
            User
        """
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalar()
    
    @staticmethod
    async def get_user_by_login(login: str) -> User:
        """Получить user по login
        Args:
            login: str - login пользователя
        Returns:
            User
        """
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.login == login)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def get_user_by_email(email: str) -> User:
        """Получить user по email
        Args:
            email: str - email пользователя
        Returns:
            User
        """
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def create_kucoin_api_key(user_id: int, name: str, api_key: str, api_secret: str, api_passphrase: str, 
                                   limit_requests: int = 1000, timedelta_refresh: int = 60) -> KucoinApiKey:
        """Создать kucoin api key"""
        async with get_db_helper().get_session() as session:
            user = await UserQuery.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")

            keys_user = await UserQuery.get_kucoin_api_keys_by_user_id(user_id)
            if keys_user:
                if any([key.api_key == api_key for key in keys_user]):
                    raise ValueError("Kucoin api key already exists")
            
            kucoin_api_key = KucoinApiKey(user_id=user_id, 
                                          name=name,
                                          api_key=api_key, 
                                          api_secret=api_secret, 
                                          api_passphrase=api_passphrase,
                                          limit_requests=limit_requests,
                                          timedelta_refresh=timedelta_refresh)

            session.add(kucoin_api_key)
            await session.commit()
            await session.refresh(kucoin_api_key)
            return kucoin_api_key

    @staticmethod
    async def get_kucoin_api_key_by_user_id(user_id: int) -> KucoinApiKey:
        """Получить kucoin api key по user_id"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.user_id == user_id)
            result = await session.execute(query)
            return result.scalar()
    
    @staticmethod
    async def get_kucoin_api_keys_by_user_id(user_id: int) -> List[KucoinApiKey]:
        """Получить все kucoin api keys по user_id"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()
    
    @staticmethod
    async def delete_kucoin_api_key(api_key_id: int) -> bool:
        """Удалить kucoin api key по id"""
        async with get_db_helper().get_session() as session:
            query = delete(KucoinApiKey).where(KucoinApiKey.id == api_key_id)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
    
    @staticmethod
    async def toggle_kucoin_api_key_status(api_key_id: int) -> KucoinApiKey:
        """Переключить статус активности kucoin api key"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.id == api_key_id)
            result = await session.execute(query)
            api_key = result.scalar()
            
            if not api_key:
                raise ValueError("API key not found")
            
            api_key.is_active = not api_key.is_active
            await session.commit()
            await session.refresh(api_key)
            return api_key
    
    @staticmethod
    async def check_and_increment_request_count(api_key_id: int) -> bool:
        """Проверить лимиты и увеличить счетчик запросов. Возвращает True если запрос можно выполнить"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.id == api_key_id)
            result = await session.execute(query)
            api_key = result.scalar()
            
            if not api_key:
                raise ValueError("API key not found")
            
            if not api_key.is_active:
                return False
            
            now = datetime.now()
            
            # Проверяем, нужно ли сбросить счетчик
            if now >= api_key.next_refresh:
                api_key.requests_count = 0
                api_key.next_refresh = now + timedelta(minutes=api_key.timedelta_refresh)
            
            # Проверяем лимит
            if api_key.requests_count >= api_key.limit_requests:
                return False
            
            # Увеличиваем счетчик
            api_key.requests_count += 1
            await session.commit()
            return True
    
    @staticmethod
    async def get_api_key_usage_info(api_key_id: int) -> Dict[str, Any]:
        """Получить информацию о использовании API ключа"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.id == api_key_id)
            result = await session.execute(query)
            api_key = result.scalar()
            
            if not api_key:
                raise ValueError("API key not found")
            
            now = datetime.utcnow()
            time_until_refresh = api_key.next_refresh - now
            
            return {
                "requests_count": api_key.requests_count,
                "limit_requests": api_key.limit_requests,
                "remaining_requests": api_key.limit_requests - api_key.requests_count,
                "next_refresh": api_key.next_refresh,
                "time_until_refresh_minutes": max(0, int(time_until_refresh.total_seconds() / 60)),
                "is_active": api_key.is_active
            }
    
    @staticmethod
    async def update_kucoin_api_key(api_key_id: int, name: str, api_key: str = None, 
                                   api_secret: str = None, api_passphrase: str = None,
                                   limit_requests: int = None, timedelta_refresh: int = None) -> KucoinApiKey:
        """Обновить kucoin api key"""
        async with get_db_helper().get_session() as session:
            query = select(KucoinApiKey).where(KucoinApiKey.id == api_key_id)
            result = await session.execute(query)
            existing_key = result.scalar()
            
            if not existing_key:
                raise ValueError("API key not found")
            
            # Обновляем только переданные поля
            if name:
                existing_key.name = name
            if api_key:
                existing_key.api_key = api_key
            if api_secret:
                existing_key.api_secret = api_secret
            if api_passphrase:
                existing_key.api_passphrase = api_passphrase
            if limit_requests is not None:
                existing_key.limit_requests = limit_requests
            if timedelta_refresh is not None:
                existing_key.timedelta_refresh = timedelta_refresh
                # Пересчитываем время следующего обновления
                existing_key.next_refresh = datetime.utcnow() + timedelta(minutes=timedelta_refresh)
            
            await session.commit()
            await session.refresh(existing_key)
            return existing_key
        
    @staticmethod
    async def add_balance_user(user_id: int, amount: float) -> User:
        """Добавить баланс пользователю"""
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar()
            if not user:
                raise ValueError("User not found")

            user.balance += amount

            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def subtract_balance_user(user_id: int, amount: float) -> User:
        """Вычесть баланс пользователю"""
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar()
            if not user:
                raise ValueError("User not found")

            if user.balance < amount:
                raise ValueError("Insufficient balance")

            user.balance -= amount
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_balance_user(user_id: int) -> float:
        """Получить баланс пользователя"""
        async with get_db_helper().get_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar()
            if not user:
                raise ValueError("User not found")
            return user.balance