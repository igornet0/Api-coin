from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.engine import db_helper


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_helper.get_session() as session:
        yield session

