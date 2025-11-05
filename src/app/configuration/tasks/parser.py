import asyncio
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import update
import json

logger = logging.getLogger(__name__)

# from src.core import data_manager
# from backend.MMM import AgentManager  # Temporarily disabled for testing
# from Dataset import LoaderTimeLine, DatasetTimeseries  # Temporarily disabled for testing
# from train_models import Loader as TrainLoader  # Temporarily disabled for testing


import asyncio
from datetime import datetime
import logging
from billiard.exceptions import SoftTimeLimitExceeded

from src.app.celery_app import celery_app
from src.handlers.att_parser import AttParser
from src.handlers.parser_handler import Handler as HandlerParser
from celery.signals import task_retry

from src.core.database.orm import TaskQuery

logger = logging.getLogger("parser_logger.tasks")

# Перехватываем сигнал retry для предотвращения повторных попыток при SoftTimeLimitExceeded
@task_retry.connect
def on_task_retry(sender=None, task_id=None, reason=None, **kwargs):
    """Предотвращаем retry для SoftTimeLimitExceeded"""
    try:
        from billiard.exceptions import SoftTimeLimitExceeded
        if isinstance(reason, SoftTimeLimitExceeded):
            logger.warning(f"Skipping retry for task {task_id} due to SoftTimeLimitExceeded")
            # Возвращаем False чтобы предотвратить retry (но это не работает напрямую)
            # Вместо этого мы обрабатываем это в except блоке
    except Exception:
        pass

@celery_app.task(
    bind=True, 
    name="app.tasks.run_parser_task",
    max_retries=3,  # Максимальное количество попыток
    default_retry_delay=60,  # Задержка перед повтором (секунды)
    # Автоматический retry для всех исключений, кроме SoftTimeLimitExceeded
    autoretry_for=(Exception,),
    retry_backoff=True,  # Экспоненциальная задержка между попытками
    retry_backoff_max=600,  # Максимальная задержка (10 минут)
    retry_jitter=True,  # Случайная задержка для предотвращения thundering herd
    ignore_result=False,
    reject_on_worker_lost=True,  # Отклоняем задачу при потере воркера
    # Устанавливаем очень большие лимиты времени для поддержки бесконечного выполнения
    # При manual_stop=True задача может работать бесконечно
    # 10 лет в секундах (315360000 секунд) - достаточно для бесконечного выполнения
    task_time_limit=315360000,  # 10 лет в секундах (для бесконечных задач)
    task_soft_time_limit=315360000,  # 10 лет в секундах (для бесконечных задач)
)
def run_parser_task(self, parser_type: str, count: int = 100, time_parser: str = "5m",
                    pause: float = 60, miss: bool = False, last_launch: bool = False,
                    clear: bool = False, save: bool = False, save_type: str = "raw",
                    coins: list = None, manual_stop: bool = False):
    """
    Celery задача для запуска парсера
    
    Задача автоматически восстанавливается после перезагрузки сервера
    благодаря настройкам персистентности в celery_app.py
    """
    try:
        # Обновляем прогресс задачи
        self.update_state(state='PROGRESS', meta={'message': 'Инициализация парсера...'})
        
        logger.info(f"Starting parser task: {parser_type}, count={count}, time={time_parser}, coins={coins}, manual_stop={manual_stop}")
        
        # Инициализируем парсер
        parser = HandlerParser.get_parser(f"parser {parser_type}")
        
        if not parser:
            error_msg = f"Invalid parser type: {parser_type}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        att = AttParser(parser, pause, clear)
        
        # Сохраняем ссылку на задачу для проверки остановки
        att.task_instance = self
        
        # Запускаем асинхронную функцию
        # Создаем новый event loop для этой задачи
        # Важно: создаем новый экземпляр Database для корректной работы с новым event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Создаем новый экземпляр Database в контексте нового event loop
        # from src.core.database.engine import Database
        from src.core.settings import settings_app

        # local_db_helper = Database(
        #     url=settings_app.database.get_url(),
        #     echo=settings_app.database.echo,
        #     echo_pool=settings_app.database.echo_pool,
        #     pool_size=settings_app.database.pool_size,
        #     max_overflow=settings_app.database.max_overflow
        # )
        
        try:
            async def run_async_parser():
                

                await TaskQuery.update_parsing_task_status(
                    task_id=self.request.id,
                    status="in_progress",
                    progress_message="Инициализация парсера...",
                    started_at=datetime.utcnow()
                )
                
                self.update_state(state='PROGRESS', meta={'message': 'Подключение к базе данных...'})
                # await local_db_helper.init_db()
                # await att.init_db(local_db_helper)
                
                # Обновляем прогресс в БД
                # async with local_db_helper.get_session() as session:
                #     await orm_update_parsing_task_status(
                #         session=session,
                #         task_id=self.request.id,
                #         status="in_progress",
                #         progress_message="Подключение к базе данных..."
                #     )

                await TaskQuery.update_parsing_task_status(
                    task_id=self.request.id,
                    status="in_progress",
                    progress_message="Подключение к базе данных..."
                )

                # Если указаны конкретные монеты, обновляем список
                if coins:
                    self.update_state(state='PROGRESS', meta={'message': f'Установка списка монет: {coins}'})
                    await TaskQuery.update_parsing_task_status(
                        task_id=self.request.id,
                        status="in_progress",
                        progress_message=f'Установка списка монет: {coins}'
                    )
                    await att.set_coin_list(coins)
                
                # Если режим ручной остановки, устанавливаем count = -1
                actual_count = -1 if manual_stop else count
                
                self.update_state(state='PROGRESS', meta={'message': 'Запуск парсинга...'})

                await TaskQuery.update_parsing_task_status(
                    task_id=self.request.id,
                    status="in_progress",
                    progress_message="Запуск парсинга..."
                )
                
                data = await att.parse(
                    count=actual_count,
                    miss=miss,
                    last_launch=last_launch,
                    time_parser=time_parser,
                    save=save,
                    save_type=save_type,
                    manual_stop=manual_stop
                )
                
                if not data:
                    result = {"status": "completed", "result": "No data parsed"}
                    await TaskQuery.update_parsing_task_status(
                        task_id=self.request.id,
                        status="completed",
                        progress_message="Парсинг завершен, данных не найдено",
                        result=result,
                        completed_at=datetime.utcnow()
                    )
                    return result
                
                result = {}
                for coin, dataset in data.items():
                    result[coin] = {
                        "count": len(dataset) if hasattr(dataset, "__len__") else 0,
                        "type": type(dataset).__name__
                    }
                
                final_result = {"status": "completed", "result": result}
                
                # Обновляем статус в БД: успешное завершение
                # async with local_db_helper.get_session() as session:
                #     await orm_update_parsing_task_status(
                #         session=session,
                #         task_id=self.request.id,
                #         status="completed",
                #         progress_message="Парсинг успешно завершен",
                #         result=final_result,
                #         completed_at=datetime.utcnow()
                #     )

                await TaskQuery.update_parsing_task_status(
                    task_id=self.request.id,
                    status="completed",
                    progress_message="Парсинг успешно завершен",
                    result=final_result,
                    completed_at=datetime.utcnow()
                )
                
                return final_result
            
            # Запускаем асинхронную функцию с таймаутом для предотвращения зависаний
            try:
                result = loop.run_until_complete(run_async_parser())
                return result
            except asyncio.CancelledError:
                # Задача была отменена - это нормально при таймауте
                logger.warning(f"Task {self.request.id} was cancelled")
                raise
        except SoftTimeLimitExceeded as timeout_error:
            # Специальная обработка для превышения soft time limit
            # Пропускаем обработку таймаута для задач с manual_stop=True (бесконечное выполнение)
            if manual_stop:
                logger.info(f"Task {self.request.id} exceeded soft time limit but continues (manual_stop=True)")
                # Для бесконечных задач игнорируем таймаут и продолжаем работу
                # Это может произойти если глобальные лимиты все еще установлены
                # Но задача должна продолжать работать
                pass
            else:
                error_msg = f"Task exceeded soft time limit (3300s)"
                logger.warning(error_msg)
                
                # Пытаемся корректно завершить работу
                try:
                    # Отменяем все задачи в loop
                    try:
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        
                        # Даем время на завершение (но не слишком долго)
                        try:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                    except Exception:
                        pass
                    
                    # Закрываем loop
                    try:
                        if not loop.is_closed():
                            loop.close()
                    except Exception:
                        pass
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup after timeout: {cleanup_error}")
                
                # Обновляем статус в БД
                try:
                    
                    error_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(error_loop)
                    try:
                        async def update_timeout_status():
                            await TaskQuery.update_parsing_task_status(
                                task_id=self.request.id,
                                status="error",
                                progress_message=f"Задача превысила лимит времени выполнения",
                                error=error_msg,
                                completed_at=datetime.utcnow()
                            )
                        
                        error_loop.run_until_complete(update_timeout_status())
                    finally:
                        error_loop.close()
                except Exception as db_error:
                    logger.error(f"Failed to update timeout status in DB: {db_error}")
                
                # Не повторяем задачу при таймауте - это бессмысленно
                return {"status": "error", "error": error_msg, "timeout": True}
        finally:
            if 'loop' in locals() and loop and not loop.is_closed():
                try:
                    loop.close()
                except Exception as e:
                    logger.warning(f"Error closing loop: {e}")
            
    except SoftTimeLimitExceeded:
        # Пробрасываем SoftTimeLimitExceeded наверх для специальной обработки
        raise
    except Exception as e:
        error_msg = f"Error in parser task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        import traceback
        error_traceback = traceback.format_exc()
        
        # Обновляем статус в БД при ошибке
        try:
            
            error_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(error_loop)
            try:
                async def update_error_status():
                    await TaskQuery.update_parsing_task_status(
                        task_id=self.request.id,
                        status="error",
                        progress_message=f"Ошибка: {error_msg}",
                        error=error_msg,
                        traceback=error_traceback,
                        completed_at=datetime.utcnow()
                    )
                
                error_loop.run_until_complete(update_error_status())
            finally:
                error_loop.close()
        except Exception as db_error:
            logger.error(f"Failed to update error status in DB: {db_error}")
        
        return {"status": "error", "error": error_msg, "traceback": error_traceback}


async def start_process_train(train_data: dict):
    pass

# async def start_process_train(train_data: dict):
#    async with db_helper.get_session() as session:

#         # Получаем процесс
#         query = select(AgentTrain).filter(AgentTrain.id == train_data["id"])
#         query = query.options(joinedload(AgentTrain.coins))

#         query = query.options(selectinload(AgentTrain.agent)
#                               .selectinload(Agent.features)
#                               .selectinload(AgentFeature.feature_value))

#         result = await session.execute(query)
#         process = result.scalars().first()
        
#         if process and process.status == "start":
#             logger.info(f"Запуск процесса ID: {process.id}")
            
#             # Обновляем статус - начат
#             process.set_status("train")
#             agent = await orm_get_agent_by_id(session, process.agent_id)
#             agent.set_status("train")
#             agent.active = False

#             await session.commit()

#             # filename = data_manager["data"] / "t.json"
#             indecaters = {}

#             for feature in process.agent.features:
#                 parameters = {value.feature_name: value.value for value in feature.feature_value}
#                 feature_t = await orm_get_feature_by_id(session, feature.feature_id)
#                 indecaters[feature_t.name] = parameters

#             config = {"agents": [
#                 {
#                     "type": process.agent.type,
#                     "name": process.agent.name,
#                     "timetravel": process.agent.timeframe,
#                     "data_normalize": True,
#                     "mod": "train",
#                     "indecaters": indecaters
#                 }
#             ]}

#             async def load_loader(coin):
#                 tm = await orm_get_timeseries_by_coin(session, coin,
#                                                                 timeframe=process.agent.timeframe)
#                 data = await orm_get_data_timeseries(session, tm.id)
                
#                 dt = DatasetTimeseries(data)

#                 return dt
            
#             def filter_func(x):
#                 if x["open"] != "x" and isinstance(x["open"], str):
#                     logger.error(f"Data validation error: {x}")
#                     return True
#                 return x["open"] != "x"

#             loaders = [LoaderTimeLine(await load_loader(coin), 200,
#                                       filter_func, timetravel=process.agent.timeframe) for coin in process.coins]

#             agent_manager = AgentManager(config=config)
#             trin_loader = TrainLoader()

#             loader = trin_loader.load_agent_data(loaders, agent_manager.get_agents(), process.batch_size, False)

#             for data in loader:
#                 logger.debug(f"Training data batch: {data}")

#             # trin_loader._train_single_agent(agent_manager.get_agents(), loaders,
#             #                                 epochs=process.epochs,
#             #                                 batch_size=process.batch_size,
#             #                                 base_lr=process.learning_rate,
#             #                                 weight_decay=process.weight_decay,
#             #                                 patience=7,
#             #                                 mixed=True,
#             #                                 mixed_precision=True)

#             # logger.debug(f"Agent manager agents: {agent_manager.get_agents()}")

#             # with open(filename, "w") as f:

#             #     json.dump({"coins": [coin.name for coin in process.coins],
#             #                 "agent": process.agent.id,
#             #                "features": features_data}, f)
            
#             # Здесь ваша логика запуска процесса (асинхронная)
#             # Например, вызов внешнего API или запуск асинхронного кода
#             # await asyncio.sleep(600)  # Имитация длительной задачи

#             logger.info(f"Процесс ID: {process.id} завершен")
            
#             # Обновляем статус - завершен
#             process.set_status("stop")
#             agent.set_status("open")
#             agent.active = True
#             await session.commit()