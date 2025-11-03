import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from src.core.settings import settings
# from core import data_manager
from .models import Base

import logging

logger = logging.getLogger("Database")

class Database:

    def __init__(self,
                url: str,
                echo: bool = False,
                echo_pool: bool = False,
                pool_size: int = 5,
                max_overflow: int = 50,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            future=True
        )
        
        self.async_session: AsyncSession = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def init_db(self):
        await self._create_tables()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    async def _create_tables(self):
        # from .orm import orm_add_coin

        async with self.engine.begin() as conn:
            logger.info("Creating tables")
            await conn.run_sync(Base.metadata.create_all)
        
        # Миграция: исправляем nullable для полей result, error, traceback в parsing_tasks
        await self._migrate_parsing_tasks_nullable()

        # async with self.async_session() as session:
        #     for coin in data_manager.coin_list:
        #         logger.debug(f"Adding coin {coin}")
        #         await orm_add_coin(session, coin)
    
    async def _migrate_parsing_tasks_nullable(self):
        """
        Миграция: изменяем поля result, error, traceback в parsing_tasks на nullable
        """
        try:
            from sqlalchemy import text
            
            async with self.engine.begin() as conn:
                # Проверяем, существует ли таблица parsing_tasks
                check_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'parsing_tasks'
                    )
                """)
                result = await conn.execute(check_query)
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.info("Table parsing_tasks does not exist, skipping migration")
                    return
                
                # Проверяем, нужно ли изменять колонки
                check_columns_query = text("""
                    SELECT column_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'parsing_tasks'
                    AND column_name IN ('result', 'error', 'traceback')
                """)
                result = await conn.execute(check_columns_query)
                columns = {row[0]: row[1] for row in result.fetchall()}
                
                # Изменяем колонки, если они не nullable
                if 'result' in columns and columns['result'] == 'NO':
                    logger.info("Migrating: making 'result' column nullable")
                    await conn.execute(text("ALTER TABLE parsing_tasks ALTER COLUMN result DROP NOT NULL"))
                
                if 'error' in columns and columns['error'] == 'NO':
                    logger.info("Migrating: making 'error' column nullable")
                    await conn.execute(text("ALTER TABLE parsing_tasks ALTER COLUMN error DROP NOT NULL"))
                
                if 'traceback' in columns and columns['traceback'] == 'NO':
                    logger.info("Migrating: making 'traceback' column nullable")
                    await conn.execute(text("ALTER TABLE parsing_tasks ALTER COLUMN traceback DROP NOT NULL"))
                
                logger.info("Migration completed successfully")
                
        except Exception as e:
            logger.warning(f"Migration failed (this is OK if columns are already correct): {e}")

# print("settings.database.get_url()")
# print(settings.database.get_url())
db_helper = Database(
    url=settings.database.get_url(),
    echo=settings.database.echo,
    echo_pool=settings.database.echo_pool,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow
)