# ============================================
# Stage 1: Build stage - для компиляции пакетов
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Установка build-зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
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
RUN pip install --no-cache-dir poetry==1.8.3

# Копирование файлов конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Настройка окружения для сборки
ENV UVLOOP_NO_EXTENSIONS=1
ENV WATCHFILES_NO_BUILD=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Увеличиваем параллельность для ускорения (используем 2 ядра вместо 1)
ENV MAKEFLAGS=-j2

# Настройка Poetry
RUN poetry config virtualenvs.create false && \
    poetry config cache-dir /tmp/poetry-cache

# Установка зависимостей через Poetry с кешированием
# Используем --prefer-binary для ускорения установки
RUN POETRY_NO_INTERACTION=1 \
    poetry install --without dev,gui --no-ansi --no-root && \
    pip uninstall -y uvloop 2>/dev/null || true && \
    # Удаление ненужных файлов для уменьшения размера образа
    find /usr/local/lib/python3.12/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type f -name "*.pyo" -delete 2>/dev/null || true && \
    # Удаление документации и примеров (НЕ удаляем .dist-info и .egg-info - они нужны для импорта)
    find /usr/local/lib/python3.12/site-packages -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -type d -name "example" -exec rm -rf {} + 2>/dev/null || true

# ============================================
# Stage 2: Runtime stage - минимальный образ
# ============================================
FROM python:3.12-slim

WORKDIR /app

# Установка только runtime зависимостей (без build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* /var/tmp/*

# Копирование установленных пакетов из builder stage
# Используем --chown для правильных прав доступа
# Используем --link для ускорения копирования (hard links вместо копирования)
COPY --from=builder --chown=root:root /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chown=root:root /usr/local/bin /usr/local/bin

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Копирование исходного кода
COPY src/ ./src/
COPY settings/ ./settings/
COPY run_app.py ./

# Создание директорий для данных и логов
RUN mkdir -p /app/data/{raw,processed,cached,backup,trach,log} && \
    find /usr/local/lib/python3.12 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12 -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.12 -type f -name "*.pyo" -delete 2>/dev/null || true

# Порт для FastAPI
EXPOSE 8000

# Команда по умолчанию
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]