# файл для query запросов
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from src.core.database.models import (Coin, Timeseries, DataTimeseries)

class PriceData(BaseModel):
    price_now: float
    max_price_now: float
    min_price_now: float
    open_price_now: float
    volume_now:float

"""
ORM запросы для работы с монетами и тикерами KuCoin
"""

from src.core.database import get_db_helper

class CoinQuery:
    """Класс для работы с запросами к таблице монет"""

    @staticmethod
    async def get_coin_by_id(coin_id: int) -> Optional[Coin]:
        """Получить монету по ID"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.id == coin_id)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def get_coin_by_symbol(symbol: str, 
                                 is_active: bool = None, 
                                 parsed: bool = None, 
                                 type_market: Literal["spot", "future"] = None) -> Optional[Coin]:
        """Получить монету по символу (например, BTC-USDT)"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.symbol == symbol)
            if is_active:
                query = query.where(Coin.is_active == is_active)
            if parsed:
                query = query.where(Coin.parsed == parsed)
            if type_market:
                query = query.where(Coin.type == type_market)
            result = await session.execute(query)

            return result.scalar()

    @staticmethod
    async def get_all_coins(limit: int = 100, offset: int = 0) -> List[Coin]:
        """Получить все монеты с пагинацией"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.is_active == True).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_coins_by_symbols(symbols: List[str]) -> List[Coin]:
        """Получить монеты по списку символов"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.symbol.in_(symbols))
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_or_update_coin_from_ticker(ticker_data: Dict[str, Any]) -> Coin:
        """
        Создать или обновить монету из данных тикера KuCoin
        
        Args:
            ticker_data: Данные тикера от KuCoin API
            
        Returns:
            Coin: Обновленная или созданная монета
        """
        async with get_db_helper().get_session() as session:
            symbol = ticker_data.get('symbol')
            if not symbol:
                raise ValueError("Symbol is required in ticker data")

            # Проверяем, существует ли монета
            print(f"{symbol=}")
            existing_coin = await CoinQuery.get_coin_by_symbol(symbol)
            print(ticker_data)
            if existing_coin:
                # Обновляем существующую монету
                update_data = {
                    'name': ticker_data.get('symbolName', symbol),
                    'last_price': float(ticker_data.get('last', 0)),
                    'buy_price': float(ticker_data.get('buy', 0)),
                    'sell_price': float(ticker_data.get('sell', 0)),
                    'volume': float(ticker_data.get('vol', 0)),
                    'volume_value': float(ticker_data.get('volValue', 0)),
                    'last_size': float(ticker_data.get('lastSize', 0)),
                    'change_rate': float(ticker_data.get('changeRate', 0)),
                    'change_price': float(ticker_data.get('changePrice', 0)),
                    'open_price': float(ticker_data.get('open', 0)),
                    'high_price': float(ticker_data.get('high', 0)),
                    'low_price': float(ticker_data.get('low', 0)),
                    'average_price': float(ticker_data.get('averagePrice', 0)),
                    'best_bid_size': float(ticker_data.get('bestBidSize', 0)),
                    'best_ask_size': float(ticker_data.get('bestAskSize', 0)),
                    'taker_fee_rate': float(ticker_data.get('takerFeeRate', 0)),
                    'maker_fee_rate': float(ticker_data.get('makerFeeRate', 0)),
                    'last_updated': datetime.now(),
                    'is_active': True,
                    # Legacy fields для совместимости
                    'price_now': float(ticker_data.get('last', 0)),
                    'max_price_now': float(ticker_data.get('high', 0)),
                    'min_price_now': float(ticker_data.get('low', 0)),
                    'open_price_now': float(ticker_data.get('open', 0)),
                    'volume_now': float(ticker_data.get('vol', 0)),
                }
                
                query = update(Coin).where(Coin.id == existing_coin.id).values(**update_data)
                await session.execute(query)
                await session.commit()
                await session.refresh(existing_coin)
                return existing_coin
            else:
                # Создаем новую монету
                new_coin = Coin(
                    symbol=symbol,
                    type=ticker_data.get('type', symbol),
                    name=ticker_data.get('symbolName', symbol),
                    last_price=float(ticker_data.get('last', 0)),
                    buy_price=float(ticker_data.get('buy', 0)),
                    sell_price=float(ticker_data.get('sell', 0)),
                    volume=float(ticker_data.get('vol', 0)),
                    volume_value=float(ticker_data.get('volValue', 0)),
                    last_size=float(ticker_data.get('lastSize', 0)),
                    change_rate=float(ticker_data.get('changeRate', 0)),
                    change_price=float(ticker_data.get('changePrice', 0)),
                    open_price=float(ticker_data.get('open', 0)),
                    high_price=float(ticker_data.get('high', 0)),
                    low_price=float(ticker_data.get('low', 0)),
                    average_price=float(ticker_data.get('averagePrice', 0)),
                    best_bid_size=float(ticker_data.get('bestBidSize', 0)),
                    best_ask_size=float(ticker_data.get('bestAskSize', 0)),
                    taker_fee_rate=float(ticker_data.get('takerFeeRate', 0)),
                    maker_fee_rate=float(ticker_data.get('makerFeeRate', 0)),
                    is_active=True,
                    # Legacy fields для совместимости
                    price_now=float(ticker_data.get('last', 0)),
                    max_price_now=float(ticker_data.get('high', 0)),
                    min_price_now=float(ticker_data.get('low', 0)),
                    open_price_now=float(ticker_data.get('open', 0)),
                    volume_now=float(ticker_data.get('vol', 0)),
                    parsed=True
                )
                
                session.add(new_coin)
                await session.commit()
                await session.refresh(new_coin)
                return new_coin

    @staticmethod
    async def update_price_coin(coin_id: int, price: float) -> Coin:
        """Обновить цену монеты"""
        async with get_db_helper().get_session() as session:
            query = update(Coin).where(Coin.id == coin_id).values(last_price=price)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def bulk_update_tickers(tickers_data: List[Dict[str, Any]]) -> List[Coin]:
        """
        Массовое обновление тикеров
        
        Args:
            tickers_data: Список данных тикеров от KuCoin API
            
        Returns:
            List[Coin]: Список обновленных монет
        """
        updated_coins = []
        
        for ticker_data in tickers_data:
            try:
                coin = await CoinQuery.create_or_update_coin_from_ticker(ticker_data)
                updated_coins.append(coin)
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку остальных
                print(f"Error updating ticker {ticker_data.get('symbol', 'unknown')}: {e}")
                continue
        
        return updated_coins
    
    @staticmethod
    async def coins_add(coins: List, type_coins: str = "spot"):
        async with get_db_helper().get_session() as session:
            for coin in coins:
                existing_coin = await CoinQuery.get_coin_by_symbol(coin.get('symbol'))
                if existing_coin:
                    continue
                session.add(Coin(type=type_coins,
                                 symbol=coin.get('symbol'),
                                 name=coin.get('name', f"{type_coins}_{coin.get('symbol')}")
                                 ))
            
                await session.commit()

    @staticmethod
    async def get_top_volume_coins(limit: int = 50) -> List[Coin]:
        """Получить топ монет по объему торгов"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(Coin.is_active == True)
                .order_by(Coin.volume_value.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_top_gainers(limit: int = 50) -> List[Coin]:
        """Получить топ монеты по росту цены"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(Coin.is_active == True)
                .order_by(Coin.change_rate.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_top_losers(limit: int = 50) -> List[Coin]:
        """Получить топ монеты по падению цены"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(Coin.is_active == True)
                .order_by(Coin.change_rate.asc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def search_coins_by_symbol(search_term: str, limit: int = 20) -> List[Coin]:
        """Поиск монет по символу"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(
                    Coin.is_active == True,
                    Coin.symbol.ilike(f"%{search_term.upper()}%")
                )
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def deactivate_old_coins(hours_threshold: int = 24) -> int:
        """
        Деактивировать монеты, которые не обновлялись более указанного времени
        
        Args:
            hours_threshold: Количество часов без обновления
            
        Returns:
            int: Количество деактивированных монет
        """
        async with get_db_helper().get_session() as session:

            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            
            query = (
                update(Coin)
                .where(
                    Coin.is_active == True,
                    Coin.last_updated < threshold_time
                )
                .values(is_active=False)
            )
            result = await session.execute(query)
            await session.commit()
            return result.rowcount

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

async def orm_get_all_data_timeseries_by_coin(session: AsyncSession, coin: Coin | str):
    """
    Получить все DataTimeseries для монеты через все её timeseries
    """
    if isinstance(coin, str):
        coin = await orm_get_coin_by_name(session, coin)
        
    if not coin:
        raise ValueError(f"Coin {coin} not found")
    
    # Получаем все timeseries для монеты
    timeseries_list = await orm_get_timeseries_by_coin(session, coin)
    
    if not timeseries_list:
        return []
    
    # Получаем все DataTimeseries для всех timeseries
    timeseries_ids = [ts.id for ts in timeseries_list]
    
    query = select(DataTimeseries).where(
        DataTimeseries.timeseries_id.in_(timeseries_ids)
    ).order_by(DataTimeseries.datetime)
    
    result = await session.execute(query)
    return result.scalars().all()