# файл для query запросов
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from core.database.models import (Coin, Timeseries, DataTimeseries)
from core.database import get_db_helper

class PriceData(BaseModel):
    price_now: float
    max_price_now: float
    min_price_now: float
    open_price_now: float
    volume_now: float

db_helper = get_db_helper()


class CoinQuery:
    """Класс для работы с запросами к базе данных монет"""
    
    async def get_coins(self, skip: int = 0, limit: int = 100, parsed_only: Optional[bool] = None) -> List[Coin]:
        """Получить список монет с пагинацией"""
        async with db_helper.get_session() as session:
            query = select(Coin)
            
            if parsed_only is not None:
                query = query.where(Coin.parsed == parsed_only)
            
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_coin_by_id(self, coin_id: int) -> Optional[Coin]:
        """Получить монету по ID"""
        async with db_helper.get_session() as session:
            query = select(Coin).where(Coin.id == coin_id)
            result = await session.execute(query)
            return result.scalar()
    
    async def get_coin_by_name(self, name: str) -> Optional[Coin]:
        """Получить монету по имени"""
        async with db_helper.get_session() as session:
            query = select(Coin).where(Coin.name == name)
            result = await session.execute(query)
            return result.scalar()
    
    async def get_or_create_coin(self, coin_data: Dict[str, Any]) -> Coin:
        """Получить или создать монету"""
        async with db_helper.get_session() as session:
            # Проверяем, существует ли монета
            existing_coin = await self.get_coin_by_name(coin_data["name"])
            
            if existing_coin:
                # Обновляем существующую монету
                for key, value in coin_data.items():
                    if hasattr(existing_coin, key):
                        setattr(existing_coin, key, value)
                await session.commit()
                await session.refresh(existing_coin)
                return existing_coin
            else:
                # Создаем новую монету
                new_coin = Coin(**coin_data)
                session.add(new_coin)
                await session.commit()
                await session.refresh(new_coin)
                return new_coin
    
    async def update_coin(self, coin_id: int, coin_data: Dict[str, Any]) -> Optional[Coin]:
        """Обновить данные монеты"""
        async with db_helper.get_session() as session:
            coin = await self.get_coin_by_id(coin_id)
            if not coin:
                return None
            
            for key, value in coin_data.items():
                if hasattr(coin, key):
                    setattr(coin, key, value)
            
            await session.commit()
            await session.refresh(coin)
            return coin
    
    async def delete_coin(self, coin_id: int) -> bool:
        """Удалить монету"""
        async with db_helper.get_session() as session:
            coin = await self.get_coin_by_id(coin_id)
            if not coin:
                return False
            
            await session.delete(coin)
            await session.commit()
            return True
    
    async def get_coin_timeseries(self, coin_id: int) -> List[Timeseries]:
        """Получить временные ряды для монеты"""
        async with db_helper.get_session() as session:
            query = select(Timeseries).where(Timeseries.coin_id == coin_id)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def create_timeseries(self, coin_id: int, timeseries_data: Dict[str, Any]) -> Timeseries:
        """Создать временной ряд для монеты"""
        async with db_helper.get_session() as session:
            timeseries = Timeseries(coin_id=coin_id, **timeseries_data)
            session.add(timeseries)
            await session.commit()
            await session.refresh(timeseries)
            return timeseries
    
    async def get_coins_stats(self) -> Dict[str, Any]:
        """Получить статистику по монетам"""
        async with db_helper.get_session() as session:
            # Общее количество монет
            total_query = select(func.count(Coin.id))
            total_result = await session.execute(total_query)
            total_coins = total_result.scalar()
            
            # Количество активных монет
            active_query = select(func.count(Coin.id)).where(Coin.parsed == True)
            active_result = await session.execute(active_query)
            active_coins = active_result.scalar()
            
            # Средняя цена
            avg_price_query = select(func.avg(Coin.price_now)).where(Coin.price_now > 0)
            avg_price_result = await session.execute(avg_price_query)
            avg_price = avg_price_result.scalar() or 0
            
            return {
                "total_coins": total_coins,
                "active_coins": active_coins,
                "inactive_coins": total_coins - active_coins,
                "average_price": float(avg_price)
            }

##################### Добавляем монеты в БД #####################################

async def orm_add_coin(
        session: AsyncSession,
        name: str,
        price_now: float = 0
) -> Coin:
    
    query = select(Coin).where(Coin.name == name)
    result = await session.execute(query)

    if not result.scalars().first():
        session.add(
            Coin(name=name,
                 price_now=price_now)
        )
        await session.commit()
    
    return await orm_get_coin_by_name(session, name)

async def orm_get_coin_by_name(session: AsyncSession, name: str) -> Coin:
    query = select(Coin).where(Coin.name == name)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_coins(session: AsyncSession) -> Coin:
    query = select(Coin)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_change_parsing_status_coin(session: AsyncSession, name: str, status: bool) -> Coin:
    query = update(Coin).where(Coin.name == name).values(parsed=status)
    await session.execute(query)
    await session.commit()

async def orm_update_coin_price(session: AsyncSession, name: str, price_data: PriceData):
    query = update(Coin).where(Coin.name == name).values(price_now=price_data.price_now,
                                                          max_price_now=price_data.max_price_now,
                                                          min_price_now=price_data.min_price_now,
                                                          open_price_now=price_data.open_price_now,
                                                          volume_now=price_data.volume_now)
    await session.execute(query)
    await session.commit()

async def orm_add_timeseries(session: AsyncSession, coin: Coin | str, timestamp: str, path_dataset: str):
    if isinstance(coin, str):
        coin = await orm_get_coin_by_name(session, coin)

    if not coin:
        raise ValueError(f"Coin {coin} not found")
    
    tm = await orm_get_timeseries_by_coin(session, coin, timestamp)

    if tm:
        return await orm_update_timeseries_path(session, tm.id, path_dataset)

    timeseries = Timeseries(coin_id=coin.id, 
                            timestamp=timestamp, 
                            path_dataset=path_dataset)
    session.add(timeseries)
    await session.commit()

    await session.refresh(timeseries)

    return timeseries

async def orm_update_timeseries_path(session: AsyncSession, timeseries_id: int, path_dataset: str):
    query = update(Timeseries).where(Timeseries.id == timeseries_id).values(path_dataset=path_dataset)
    await session.execute(query)
    await session.commit()

async def orm_get_timeseries_by_path(session: AsyncSession, path_dataset: str):
    query = select(Timeseries).where(Timeseries.path_dataset == path_dataset)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_timeseries_by_id(session: AsyncSession, id: int):
    query = select(Timeseries).where(Timeseries.id == id)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_timeseries_by_coin(session: AsyncSession, coin: Coin | str, timestamp: str = None):
    if isinstance(coin, str):
        coin = await orm_get_coin_by_name(session, coin)

        if not coin:
            raise ValueError(f"Coin {coin} not found")
        
    if timestamp:
        query = select(Timeseries).options(joinedload(Timeseries.coin)).where(Timeseries.coin_id == coin.id, Timeseries.timestamp == timestamp)
        result = await session.execute(query)
        return result.scalars().first()
    
    query = select(Timeseries).options(joinedload(Timeseries.coin)).where(Timeseries.coin_id == coin.id)
    result = await session.execute(query)

    return result.scalars().all()

async def orm_get_data_timeseries(session: AsyncSession, timeseries_id: int):
    query = select(DataTimeseries).where(DataTimeseries.timeseries_id == timeseries_id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_data_timeseries_by_datetime(session: AsyncSession, timeseries_id: int, datetime: datetime):
    query = select(DataTimeseries).where(DataTimeseries.timeseries_id == timeseries_id, DataTimeseries.datetime == datetime)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_add_data_timeseries(session: AsyncSession, timeseries_id: int, data_timeseries: dict):
    dt = await orm_get_data_timeseries_by_datetime(session, timeseries_id, data_timeseries["datetime"])

    if dt:
        return False
    
    session.add(DataTimeseries(timeseries_id=timeseries_id, **data_timeseries))
    await session.commit()

    return True