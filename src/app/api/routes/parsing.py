from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas import ParsingTaskRequest, ParsingTaskResponse, TaskStatusResponse, ParsingTaskListItem
from src.app.celery_app import celery_app
from src.app.tasks import run_parser_task
from src.handlers.parser_handler import Handler as HandlerParser
from src.core.database.engine import db_helper
from src.core.database.orm import orm_create_parsing_task, orm_get_parsing_task_by_task_id, orm_get_all_parsing_tasks

router = APIRouter(prefix="/parsing", tags=["parsing"])


async def get_db_session():
    """Dependency для получения сессии БД"""
    async with db_helper.get_session() as session:
        yield session


@router.post("/start", response_model=ParsingTaskResponse)
async def start_parsing(
    task_request: ParsingTaskRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Запустить задачу парсинга через Celery и создать запись в БД
    """
    # Проверяем доступность парсера
    available_parsers = HandlerParser.get_available_parsers()
    parser_full_name = f"parser {task_request.parser_type}"
    
    if parser_full_name not in available_parsers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parser type: {task_request.parser_type}. Available: {[p.replace('parser ', '') for p in available_parsers]}"
        )
    
    # Запускаем задачу Celery
    task = run_parser_task.delay(
        parser_type=task_request.parser_type,
        count=task_request.count,
        time_parser=task_request.time_parser,
        pause=task_request.pause,
        miss=task_request.miss,
        last_launch=task_request.last_launch,
        clear=task_request.clear,
        save=task_request.save,
        save_type=task_request.save_type,
        coins=task_request.coins,
        manual_stop=task_request.manual_stop
    )
    
    # Создаем запись в БД
    db_task = await orm_create_parsing_task(
        session=session,
        task_id=task.id,
        parser_type=task_request.parser_type,
        count=task_request.count,
        time_parser=task_request.time_parser,
        pause=task_request.pause,
        miss=task_request.miss,
        last_launch=task_request.last_launch,
        clear=task_request.clear,
        save=task_request.save,
        save_type=task_request.save_type,
        coins=task_request.coins,
        manual_stop=task_request.manual_stop,
    )
    
    return ParsingTaskResponse(
        task_id=task.id,
        status=task.status,
        message=f"Parsing task {task.id} started"
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Получить статус задачи парсинга из БД (с приоритетом) или из Celery
    """
    # Сначала пытаемся получить из БД
    db_task = await orm_get_parsing_task_by_task_id(session, task_id)
    
    if db_task:
        # Если задача найдена в БД, возвращаем статус из БД
        response = {
            "task_id": task_id,
            "status": db_task.status,
            "result": db_task.result,
            "error": db_task.error,
            "message": db_task.progress_message,
            "traceback": db_task.traceback,
            "created_at": db_task.created_at,
            "started_at": db_task.started_at,
            "completed_at": db_task.completed_at
        }
        return TaskStatusResponse(**response)
    
    # Если не найдено в БД, проверяем Celery
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == "PENDING":
        response = {
            "task_id": task_id,
            "status": "pending",
            "result": None,
            "error": None
        }
    elif task_result.state == "PROGRESS":
        progress_info = task_result.info if isinstance(task_result.info, dict) else {}
        response = {
            "task_id": task_id,
            "status": "in_progress",
            "result": progress_info,
            "error": None,
            "message": progress_info.get("message", "Выполняется...")
        }
    elif task_result.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "status": "completed",
            "result": task_result.result if isinstance(task_result.result, dict) else {"result": task_result.result},
            "error": None
        }
    else:
        error_info = task_result.info
        error_message = "Unknown error"
        error_traceback = None
        
        if isinstance(error_info, dict):
            error_message = error_info.get("error", str(error_info))
            error_traceback = error_info.get("traceback")
        elif error_info:
            error_message = str(error_info)
        
        response = {
            "task_id": task_id,
            "status": task_result.state.lower(),
            "result": None,
            "error": error_message,
            "traceback": error_traceback
        }
    
    return TaskStatusResponse(**response)


@router.get("/tasks", response_model=list[ParsingTaskListItem])
async def get_tasks(
    limit: int = 50,
    status: str = None,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Получить список задач парсинга из БД
    """
    tasks = await orm_get_all_parsing_tasks(
        session=session,
        limit=limit,
        status=status
    )
    
    return [
        ParsingTaskListItem(
            task_id=task.task_id,
            parser_type=task.parser_type,
            status=task.status,
            progress_message=task.progress_message,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            manual_stop=task.manual_stop,
            coins=task.coins if isinstance(task.coins, list) else None
        )
        for task in tasks
    ]


@router.post("/stop/{task_id}", response_model=Dict[str, str])
async def stop_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Остановить задачу парсинга и обновить статус в БД
    """
    # Отменяем задачу в Celery
    celery_app.control.revoke(task_id, terminate=True)
    
    # Обновляем статус в БД
    from src.core.database.orm import orm_update_parsing_task_status
    from datetime import datetime
    await orm_update_parsing_task_status(
        session=session,
        task_id=task_id,
        status="revoked",
        progress_message="Задача была остановлена пользователем",
        completed_at=datetime.utcnow()
    )
    
    return {
        "task_id": task_id,
        "status": "revoked",
        "message": f"Task {task_id} has been revoked"
    }

