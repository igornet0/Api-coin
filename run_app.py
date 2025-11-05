# #!/usr/bin/env python
# """
# Скрипт для запуска FastAPI приложения
# """
# import uvicorn

# from src.core import settings_app, load_database

# if __name__ == "__main__":
#     load_database()
    
#     uvicorn.run(
#         "src.app.main:app",
#         host=settings_app.app.host,
#         port=settings_app.app.port,
#         reload=settings_app.app.reload,
#         log_level=settings_app.logging.level.lower(),
#         workers=settings_app.app.workers,
#         limit_concurrency=settings_app.app.limit_concurrency,
#     )

#!/usr/bin/env python3
"""
Главный файл для запуска KuCoin API сервера
"""
import argparse
import uvicorn
import sys
import os

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Основная функция для запуска приложения"""
    # Парсинг аргументов командной строки
    # parser = argparse.ArgumentParser(description="KuCoin API Server")
    # parser.add_argument("--env", action="store", default=None, 
    #                     choices=["dev", "prod"], 
    #                     help="Environment (dev/prod). If not specified, will be determined from ENVIRONMENT or ENV variable, defaulting to 'dev'")
    # args = parser.parse_args()
    
    # Загружаем настройки с переданным env
    from core.settings import settings_app
    # settings = auto_load_settings(args.env)
    
    # Инициализация базы данных
    from core.database import load_database
    load_database()
    
    # Создание приложения
    from app.create_app import create_app
    app = create_app()
    
    # Запуск сервера
    uvicorn.run(
        "run_app:app",
        host=settings_app.app.host,
        port=settings_app.app.port,
        reload=settings_app.app.reload,
        log_level=settings_app.logging.level.lower(),
        workers=settings_app.app.workers,
        limit_concurrency=settings_app.app.limit_concurrency,
    )
    
    return app

# # Загружаем настройки для использования uvicorn при импорте модуля
# from core.settings import auto_load_settings

# # Определяем env для модульного уровня (когда файл импортируется)
# # Пробуем получить из аргументов командной строки, если они есть
# env = None
# if "--env" in sys.argv:
#     try:
#         env_index = sys.argv.index("--env")
#         if env_index + 1 < len(sys.argv):
#             env_arg = sys.argv[env_index + 1]
#             if env_arg in ["dev", "prod"]:
#                 env = env_arg
#     except (ValueError, IndexError):
#         pass

# settings = auto_load_settings(env)

# # Инициализация для модульного импорта
from core.database import load_database
load_database()

from app.create_app import create_app
app = create_app()

if __name__ == "__main__":
    main()
