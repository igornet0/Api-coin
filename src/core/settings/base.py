from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Определяем путь к файлу конфигурации относительно корня проекта
# config.py находится в src/core/settings/, а prod.env в settings/
def _find_config_file() -> Path:
    """Находит файл конфигурации независимо от рабочей директории"""
    # Путь относительно расположения config.py (надежный способ - всегда работает)
    # __file__ = src/core/settings/config.py
    # parent = src/core/settings/
    # parent.parent = src/core/
    # parent.parent.parent = src/
    # parent.parent.parent.parent = корень проекта
    config_file_from_module = BASE_DIR / "settings" / "prod.env"
    
    # Проверяем существование с абсолютным путем
    abs_path = config_file_from_module.resolve()
    if abs_path.exists():
        return abs_path
    
    # Пробуем относительно текущей рабочей директории
    config_file_from_cwd = Path.cwd() / "settings" / "prod.env"
    abs_path_cwd = config_file_from_cwd.resolve()
    if abs_path_cwd.exists():
        return abs_path_cwd
    
    # Пробуем на уровень выше (для запуска из src/)
    config_file_from_parent = Path.cwd().parent / "settings" / "prod.env"
    abs_path_parent = config_file_from_parent.resolve()
    if abs_path_parent.exists():
        return abs_path_parent
    
    # Если ничего не найдено, возвращаем путь относительно модуля (будет ошибка при загрузке)
    # Но это должно работать, так как это абсолютный путь
    return abs_path

_CONFIG_FILE = _find_config_file()

# Для отладки: убедимся, что файл найден
if not _CONFIG_FILE.exists():
    import sys
    print(f"ERROR: Config file not found at {_CONFIG_FILE}", file=sys.stderr)
    print(f"Current working directory: {Path.cwd()}", file=sys.stderr)
    print(f"Config file location: {Path(__file__).resolve()}", file=sys.stderr)
    raise FileNotFoundError(f"Configuration file not found: {_CONFIG_FILE}")

class AppBaseConfig:
    """Базовый класс для конфигурации с общими настройками"""
    case_sensitive = False
    env_file = str(_CONFIG_FILE)
    env_file_encoding = "utf-8"
    env_nested_delimiter="__"
    extra = "ignore"