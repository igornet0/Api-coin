# файл для query запросов
from datetime import datetime, timedelta
from typing import Literal, Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from src.core.database.models import (User, KucoinApiKey, Order)
from src.core.database import db_helper

class OrderQuery:
    """Класс для работы с запросами к базе данных orders"""

    @staticmethod
    async def create_order(user_id: int, kucoin_api_key_id: int, exchange_order_id: str, coin_id: int, order_type: str, side: str, size: float, price: float) -> Order:
        """Создать ордер
        Args:
            user_id: int - id пользователя
            kucoin_api_key_id: int - id kucoin api ключа
            exchange_order_id: str - id ордера на бирже KuCoin
            coin_id: int - id монеты
            order_type: str - тип ордера (limit или market)
            side: str - сторона ордера (buy или sell)
            size: float - размер ордера
            price: float - цена ордера
        Returns:
            Order
        """
        async with db_helper.get_session() as session:
            order = Order(
                user_id=user_id, 
                kucoin_api_key_id=kucoin_api_key_id,
                exchange_order_id=exchange_order_id,
                coin_id=coin_id, 
                order_type=order_type, 
                side=side, 
                size=size, 
                price=price, 
                status='open'
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order
    
    @staticmethod
    async def get_order_by_id(order_id: int) -> Order:
        """Получить ордер по id"""
        async with db_helper.get_session() as session:
            query = select(Order).where(Order.id == order_id)
            result = await session.execute(query)
            return result.scalar()
    
    @staticmethod
    async def get_orders_by_user_id(user_id: int) -> List[Order]:
        """Получить все ордера по user_id"""
        async with db_helper.get_session() as session:
            query = select(Order).where(Order.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()
    
    @staticmethod
    async def update_status_order(order_id: int, status: Literal['open', 'closed', 'cancelled']) -> Order:
        """Обновить статус ордера"""
        async with db_helper.get_session() as session:
            query = update(Order).where(Order.id == order_id).values(status=status)
            result = await session.execute(query)
            await session.commit()
            return result.scalar()
    
    @staticmethod
    async def update_order_size(order_id: int, size: float) -> Order:
        """Обновить размер ордера"""
        async with db_helper.get_session() as session:
            query = update(Order).where(Order.id == order_id).values(size=size)
            result = await session.execute(query)
            await session.commit()
            return result.scalar()

    @staticmethod
    async def get_orders(user_id: int, coin_id: int) -> List[Order]:
        """Получить все ордера по user_id и coin_id"""
        async with db_helper.get_session() as session:
            query = select(Order).where(Order.user_id == user_id, Order.coin_id == coin_id)
            result = await session.execute(query)
            return result.scalars().all()