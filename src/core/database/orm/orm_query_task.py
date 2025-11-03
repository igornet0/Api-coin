# ORM функции для работы с задачами парсинга
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import ParsingTask


async def orm_create_parsing_task(
    session: AsyncSession,
    task_id: str,
    parser_type: str,
    count: int = 100,
    time_parser: str = "5m",
    pause: float = 60.0,
    miss: bool = False,
    last_launch: bool = False,
    clear: bool = False,
    save: bool = False,
    save_type: str = "raw",
    coins: Optional[list] = None,
    manual_stop: bool = False,
) -> ParsingTask:
    """
    Создать новую задачу парсинга в БД
    """
    parsing_task = ParsingTask(
        task_id=task_id,
        parser_type=parser_type,
        count=count,
        time_parser=time_parser,
        pause=pause,
        miss=miss,
        last_launch=last_launch,
        clear=clear,
        save=save,
        save_type=save_type,
        coins=coins,
        manual_stop=manual_stop,
        status="pending",
    )
    session.add(parsing_task)
    await session.commit()
    await session.refresh(parsing_task)
    return parsing_task


async def orm_get_parsing_task_by_task_id(
    session: AsyncSession,
    task_id: str
) -> Optional[ParsingTask]:
    """
    Получить задачу парсинга по Celery task_id
    """
    query = select(ParsingTask).where(ParsingTask.task_id == task_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def orm_get_parsing_task_by_id(
    session: AsyncSession,
    task_db_id: int
) -> Optional[ParsingTask]:
    """
    Получить задачу парсинга по ID в БД
    """
    query = select(ParsingTask).where(ParsingTask.id == task_db_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def orm_update_parsing_task_status(
    session: AsyncSession,
    task_id: str,
    status: str,
    progress_message: Optional[str] = None,
    result: Optional[dict] = None,
    error: Optional[str] = None,
    traceback: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
) -> Optional[ParsingTask]:
    """
    Обновить статус задачи парсинга
    """
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow(),
    }
    
    if progress_message is not None:
        update_data["progress_message"] = progress_message
    if result is not None:
        update_data["result"] = result
    if error is not None:
        update_data["error"] = error
    if traceback is not None:
        update_data["traceback"] = traceback
    if started_at is not None:
        update_data["started_at"] = started_at
    if completed_at is not None:
        update_data["completed_at"] = completed_at
    
    query = (
        update(ParsingTask)
        .where(ParsingTask.task_id == task_id)
        .values(**update_data)
    )
    await session.execute(query)
    await session.commit()
    
    # Получаем обновленную задачу
    return await orm_get_parsing_task_by_task_id(session, task_id)


async def orm_get_unfinished_parsing_tasks(
    session: AsyncSession,
    include_manual_stop: bool = True
) -> list[ParsingTask]:
    """
    Получить список незавершенных задач парсинга
    
    Args:
        include_manual_stop: Если True, включает задачи с ручной остановкой
    """
    conditions = [
        ParsingTask.status.in_(["pending", "in_progress"]),
    ]
    
    if include_manual_stop:
        conditions.append(
            and_(
                ParsingTask.status.in_(["pending", "in_progress"]),
                ParsingTask.manual_stop == True
            )
        )
    
    query = select(ParsingTask).where(
        ParsingTask.status.in_(["pending", "in_progress"])
    ).order_by(ParsingTask.created_at.desc())
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def orm_get_all_parsing_tasks(
    session: AsyncSession,
    limit: Optional[int] = None,
    offset: int = 0,
    status: Optional[str] = None
) -> list[ParsingTask]:
    """
    Получить список всех задач парсинга с фильтрацией
    """
    query = select(ParsingTask)
    
    if status:
        query = query.where(ParsingTask.status == status)
    
    query = query.order_by(ParsingTask.created_at.desc())
    
    if limit:
        query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    return list(result.scalars().all())


