FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    git \
    curl \
    libffi-dev \
    libssl-dev \
    make \
    cmake \
    pkg-config \
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry==1.8.3

# Копирование файлов конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Отключаем сборку тяжёлых C-расширений и оптимизируем для ARM
ENV UVLOOP_NO_EXTENSIONS=1
ENV WATCHFILES_NO_BUILD=1
# Ограничиваем параллельную компиляцию для экономии памяти (ARM)
ENV MAKEFLAGS=-j1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Используем кеш pip для ускорения пересборки
ENV PIP_CACHE_DIR=/tmp/pip_cache

# Настройка Poetry для использования системного окружения
RUN poetry config virtualenvs.create false

# Установка критичных пакетов без uvloop (отдельный слой для кеширования)
# Для ARM: устанавливаем FastAPI и uvicorn без [standard] extra (без uvloop)
# Это предотвращает попытку компиляции uvloop на ARM архитектуре
RUN pip install --prefer-binary --cache-dir /tmp/pip_cache \
    "fastapi>=0.120.3,<0.121.0" \
    "uvicorn>=0.30.0" \
    "httptools>=0.7.0" \
    "watchfiles>=1.0.0"

# Установка зависимостей через Poetry (отдельный слой для кеширования)
RUN POETRY_NO_INTERACTION=1 \
    poetry install --without dev --no-ansi --no-root && \
    pip uninstall -y uvloop 2>/dev/null || true

# Очистка кеша pip для уменьшения размера образа
RUN rm -rf /tmp/pip_cache

# Копирование исходного кода
COPY src/ ./src/
COPY settings/ ./settings/
COPY run_app.py ./

# Создание директорий для данных и логов
RUN mkdir -p /app/data/{raw,processed,cached,backup,trach,log}

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Порт для FastAPI
EXPOSE 8000

# Команда по умолчанию
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]