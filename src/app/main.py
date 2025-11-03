from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .api.routes import coins, news, parsing
from src.core.database.engine import db_helper
from src.core.utils.configure_logging import setup_logging

import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    # Startup
    setup_logging()
    logger.info("Starting FastAPI application...")
    
    # Инициализация БД
    await db_helper.init_db()
    logger.info("Database initialized")
    
    # Восстановление незавершенных задач
    await restore_unfinished_tasks()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await db_helper.dispose()


async def restore_unfinished_tasks():
    """
    Восстановление незавершенных задач парсинга при старте приложения
    """
    try:
        from src.core.database.orm import orm_get_unfinished_parsing_tasks
        from .celery_app import celery_app
        from .tasks import run_parser_task
        from celery.result import AsyncResult
        from datetime import datetime, timedelta
        
        async with db_helper.get_session() as session:
            unfinished_tasks = await orm_get_unfinished_parsing_tasks(session)
            
            if not unfinished_tasks:
                logger.info("No unfinished tasks found")
                return
            
            logger.info(f"Found {len(unfinished_tasks)} unfinished task(s), attempting to restore...")
            
            restored_count = 0
            skip_count = 0
            now = datetime.utcnow()
            
            for task in unfinished_tasks:
                try:
                    # Защита от бесконечного цикла: не восстанавливаем задачи, созданные менее 5 минут назад
                    # Это предотвращает восстановление задач, которые были только что восстановлены
                    time_since_creation = now - task.created_at.replace(tzinfo=None) if task.created_at else timedelta(days=1)
                    if time_since_creation < timedelta(minutes=5):
                        logger.info(f"Skipping task {task.task_id}: created {time_since_creation.total_seconds():.0f} seconds ago (too recent, may be from previous restoration)")
                        skip_count += 1
                        continue
                    
                    # Проверяем, существует ли задача в Celery
                    celery_task_result = AsyncResult(task.task_id, app=celery_app)
                    
                    # Если задача уже завершена в Celery, обновляем статус в БД
                    if celery_task_result.state == "SUCCESS":
                        from src.core.database.orm import orm_update_parsing_task_status
                        await orm_update_parsing_task_status(
                            session=session,
                            task_id=task.task_id,
                            status="completed",
                            progress_message="Задача завершена при восстановлении",
                            result=celery_task_result.result if hasattr(celery_task_result, 'result') else None,
                            completed_at=datetime.utcnow()
                        )
                        logger.info(f"Task {task.task_id} was completed, updated status in DB")
                        continue
                    
                    elif celery_task_result.state == "FAILURE":
                        from src.core.database.orm import orm_update_parsing_task_status
                        error_info = celery_task_result.info
                        error_msg = str(error_info) if error_info else "Task failed"
                        await orm_update_parsing_task_status(
                            session=session,
                            task_id=task.task_id,
                            status="error",
                            progress_message=f"Задача завершилась с ошибкой: {error_msg}",
                            error=error_msg,
                            completed_at=datetime.utcnow()
                        )
                        logger.info(f"Task {task.task_id} failed, updated status in DB")
                        continue
                    
                    # Если задача в PENDING или не существует, перезапускаем её
                    # Особенно важно для задач с ручной остановкой (manual_stop=True)
                    task_state = celery_task_result.state
                    if task_state is None:
                        task_state = "UNKNOWN"
                    
                    if task.manual_stop or task_state in ("PENDING", "UNKNOWN"):
                        logger.info(f"Restoring task {task.task_id} (parser_type={task.parser_type}, manual_stop={task.manual_stop}, celery_state={task_state})")
                        
                        # Перезапускаем задачу с теми же параметрами
                        new_celery_task = run_parser_task.delay(
                            parser_type=task.parser_type,
                            count=task.count,
                            time_parser=task.time_parser,
                            pause=task.pause,
                            miss=task.miss,
                            last_launch=task.last_launch,
                            clear=task.clear,
                            save=task.save,
                            save_type=task.save_type,
                            coins=task.coins,
                            manual_stop=task.manual_stop
                        )
                        
                        # Помечаем старую задачу как восстановленную
                        from src.core.database.orm import orm_update_parsing_task_status
                        await orm_update_parsing_task_status(
                            session=session,
                            task_id=task.task_id,
                            status="completed",  # Помечаем как завершенную, чтобы не восстанавливать снова
                            progress_message=f"Задача была восстановлена при перезапуске сервера (новый task_id: {new_celery_task.id})",
                            result={"restored": True, "new_task_id": new_celery_task.id},
                            completed_at=datetime.utcnow()
                        )
                        
                        # Создаем новую запись для новой задачи Celery
                        from src.core.database.orm import orm_create_parsing_task
                        await orm_create_parsing_task(
                            session=session,
                            task_id=new_celery_task.id,
                            parser_type=task.parser_type,
                            count=task.count,
                            time_parser=task.time_parser,
                            pause=task.pause,
                            miss=task.miss,
                            last_launch=task.last_launch,
                            clear=task.clear,
                            save=task.save,
                            save_type=task.save_type,
                            coins=task.coins,
                            manual_stop=task.manual_stop
                        )
                        
                        restored_count += 1
                        logger.info(f"Task {task.task_id} restored with new Celery task {new_celery_task.id}")
                    else:
                        # Задача в другом состоянии (PROGRESS и т.д.) - возможно, она еще выполняется
                        logger.info(f"Task {task.task_id} is in state {task_state}, skipping restoration")
                    
                except Exception as e:
                    logger.error(f"Failed to restore task {task.task_id}: {e}", exc_info=True)
            
            logger.info(f"Restoration complete: {restored_count} restored, {skip_count} skipped (too recent), {len(unfinished_tasks) - restored_count - skip_count} already completed/failed")
            
    except Exception as e:
        logger.error(f"Error during task restoration: {e}", exc_info=True)


app = FastAPI(
    title="KuCoin Parser API",
    description="API для просмотра данных парсинга и управления парсингом через Celery",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(coins.router)
app.include_router(news.router)
app.include_router(parsing.router)

# Подключение статических файлов
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Главная страница с фронтендом
    """
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


@app.get("/api")
async def api_info():
    """
    Информация об API
    """
    return {
        "message": "KuCoin Parser API",
        "version": "1.0.0",
        "endpoints": {
            "coins": "/coins",
            "news": "/news",
            "parsing": "/parsing"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Проверка здоровья приложения
    """
    return {"status": "healthy"}

