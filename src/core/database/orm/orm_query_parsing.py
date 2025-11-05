# файл для query запросов
# from datetime import datetime
# from sqlalchemy import select, update, delete
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import joinedload
# from pydantic import BaseModel

# from src.core.database.models import (Coin, ParsingConfig)
# from .orm_query_coin import orm_get_coin_by_name

# class ParsingConfig(BaseModel):
#     id: int
#     name: str
#     config: dict
#     coins_list: list[str]

# async def orm_add_parsing_config(session: AsyncSession, name: str, config: dict):
#     parsing_config = ParsingConfig(name=name, config=config)
#     session.add(parsing_config)
#     await session.commit()
#     return parsing_config

# async def orm_get_parsing_config_by_name(session: AsyncSession, name: str):
#     query = select(ParsingConfig).where(ParsingConfig.name == name)
#     result = await session.execute(query)
#     return result.scalars().first()

# async def orm_get_parsing_config_by_id(session: AsyncSession, id: int):
#     query = select(ParsingConfig).where(ParsingConfig.id == id)
#     result = await session.execute(query)
#     return result.scalars().first()

# async def orm_get_parsing_config_by_coin(session: AsyncSession, coin: Coin | str):
#     if isinstance(coin, str):
#         coin = await orm_get_coin_by_name(session, coin)

#         if not coin:
#             raise ValueError(f"Coin {coin} not found")

#     query = select(ParsingConfig).options(joinedload(ParsingConfig.coins)).where(ParsingConfig.coins.any(coin_id=coin.id))
#     result = await session.execute(query)
#     return result.scalars().first()

# async def orm_add_parsing_config_coin(session: AsyncSession, parsing_config: ParsingConfig, coin: Coin | str):
#     if isinstance(coin, str):
#         coin = await orm_get_coin_by_name(session, coin)

#         if not coin:
#             raise ValueError(f"Coin {coin} not found")

#     parsing_config_coin = ParsingConfigCoin(parsing_config=parsing_config, coin=coin)
#     session.add(parsing_config_coin)
#     await session.commit()
#     return parsing_config_coin