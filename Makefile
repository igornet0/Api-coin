.PHONY: help build up down restart logs shell app-shell celery-shell ps clean test install build-local stop-local check-services start-services

# Цвета для вывода
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RED    := $(shell tput -Txterm setaf 1)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

# Переменные
DOCKER_COMPOSE = docker-compose -f docker/docker-compose.yml
APP_NAME = parser_kucoin
PYTHONPATH = $(PWD)/src:$(PWD)
PID_FILE = .pids.local
WORKING_DIR = $(PWD)/src

##@ Общая информация

help: ## Показать это сообщение помощи
	@echo ''
	@echo 'Использование:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Цели:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Локальный запуск (без Docker)

build: ## Запустить все модули проекта без Docker
	@mkdir -p logs
	@echo "${GREEN}Запуск всех модулей проекта без Docker...${RESET}"
	@make check-services
	@make start-services
	@echo "${GREEN}Проверка зависимостей...${RESET}"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "${RED}Poetry не установлен. Установите: pip install poetry${RESET}"; \
		exit 1; \
	fi
	@if [ ! -d "$$(poetry env info --path 2>/dev/null)" ]; then \
		echo "${YELLOW}Виртуальное окружение не найдено. Установка зависимостей...${RESET}"; \
		poetry install --no-root --without gui,dev; \
	fi
	@echo "${GREEN}Запуск FastAPI приложения...${RESET}"
	@cd $(WORKING_DIR) && PYTHONPATH=$(PYTHONPATH) poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/fastapi.log 2>&1 & \
		echo $$! > ../$(PID_FILE); \
		echo "FastAPI PID: $$!"
	@sleep 3
	@if ! kill -0 $$(head -1 $(PID_FILE) 2>/dev/null) 2>/dev/null; then \
		echo "${RED}✗ FastAPI не запустился! Проверьте логи:${RESET}"; \
		echo "${YELLOW}Последние строки из logs/fastapi.log:${RESET}"; \
		tail -20 logs/fastapi.log 2>/dev/null || echo "Лог файл не найден"; \
		exit 1; \
	fi
	@if ! nc -z localhost 8000 >/dev/null 2>&1; then \
		echo "${YELLOW}⚠ FastAPI процесс запущен, но порт 8000 не отвечает. Проверьте логи.${RESET}"; \
		tail -20 logs/fastapi.log 2>/dev/null || true; \
	fi
	@echo "${GREEN}Запуск Celery worker...${RESET}"
	@cd $(WORKING_DIR) && PYTHONPATH=$(PYTHONPATH) poetry run celery -A app.celery_app worker --loglevel=info --concurrency=4 > ../logs/celery.log 2>&1 & \
		echo $$! >> ../$(PID_FILE); \
		echo "Celery Worker PID: $$!"
	@sleep 2
	@echo "${GREEN}Запуск Celery beat...${RESET}"
	@cd $(WORKING_DIR) && PYTHONPATH=$(PYTHONPATH) poetry run celery -A app.celery_app beat --loglevel=info > ../logs/celery-beat.log 2>&1 & \
		echo $$! >> ../$(PID_FILE); \
		echo "Celery Beat PID: $$!"
	@sleep 1
	@echo ""
	@if nc -z localhost 8000 >/dev/null 2>&1; then \
		echo "${GREEN}✓ Все модули запущены!${RESET}"; \
		echo "${WHITE}FastAPI:${RESET} http://localhost:8000"; \
		echo "${WHITE}API Docs:${RESET} http://localhost:8000/docs"; \
	else \
		echo "${RED}✗ FastAPI не отвечает на порту 8000${RESET}"; \
		echo "${YELLOW}Проверьте логи для диагностики:${RESET}"; \
		echo "${YELLOW}  tail -f logs/fastapi.log${RESET}"; \
	fi
	@echo "${WHITE}Логи:${RESET} logs/fastapi.log, logs/celery.log, logs/celery-beat.log"
	@echo "${WHITE}PID файл:${RESET} $(PID_FILE)"
	@echo "${YELLOW}Для остановки:${RESET} make stop-local"

stop-local: ## Остановить все локальные процессы
	@echo "${YELLOW}Остановка всех локальных процессов...${RESET}"
	@if [ -f $(PID_FILE) ]; then \
		while read pid; do \
			if kill -0 $$pid 2>/dev/null; then \
				echo "Остановка процесса PID: $$pid"; \
				kill $$pid 2>/dev/null || true; \
			fi; \
		done < $(PID_FILE); \
		rm -f $(PID_FILE); \
		echo "${GREEN}Все процессы остановлены${RESET}"; \
	else \
		echo "${YELLOW}PID файл не найден. Поиск процессов по имени...${RESET}"; \
		pkill -f "uvicorn app.main:app" 2>/dev/null || true; \
		pkill -f "celery.*worker" 2>/dev/null || true; \
		pkill -f "celery.*beat" 2>/dev/null || true; \
		echo "${GREEN}Процессы остановлены${RESET}"; \
	fi

check-services: ## Проверить наличие зависимых сервисов
	@echo "${GREEN}Проверка зависимых сервисов...${RESET}"
	@FAILED=0; \
	OS="$$(uname -s)"; \
	if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1 && ! nc -z localhost 5432 >/dev/null 2>&1; then \
		echo "${RED}✗ PostgreSQL не запущен на localhost:5432${RESET}"; \
		if [ "$$OS" = "Linux" ]; then \
			echo "${YELLOW}  Запустите: sudo systemctl start postgresql${RESET}"; \
		else \
			echo "${YELLOW}  Запустите: brew services start postgresql@14${RESET}"; \
		fi; \
		FAILED=1; \
	else \
		echo "${GREEN}✓ PostgreSQL доступен${RESET}"; \
	fi; \
	if ! nc -z localhost 5672 >/dev/null 2>&1; then \
		echo "${RED}✗ RabbitMQ не запущен на localhost:5672${RESET}"; \
		if [ "$$OS" = "Linux" ]; then \
			echo "${YELLOW}  Запустите: sudo systemctl start rabbitmq-server${RESET}"; \
			echo "${YELLOW}  Или установите: sudo apt-get install -y rabbitmq-server${RESET}"; \
		else \
			echo "${YELLOW}  Запустите: brew services start rabbitmq${RESET}"; \
		fi; \
		FAILED=1; \
	else \
		echo "${GREEN}✓ RabbitMQ доступен${RESET}"; \
	fi; \
	if ! redis-cli ping >/dev/null 2>&1 && ! nc -z localhost 6379 >/dev/null 2>&1; then \
		echo "${RED}✗ Redis не запущен на localhost:6379${RESET}"; \
		if [ "$$OS" = "Linux" ]; then \
			echo "${YELLOW}  Запустите: sudo systemctl start redis-server${RESET}"; \
			echo "${YELLOW}  Или установите: sudo apt-get install -y redis-server${RESET}"; \
		else \
			echo "${YELLOW}  Запустите: brew services start redis${RESET}"; \
		fi; \
		FAILED=1; \
	else \
		echo "${GREEN}✓ Redis доступен${RESET}"; \
	fi; \
	if [ $$FAILED -eq 1 ]; then \
		echo ""; \
		echo "${YELLOW}Попытка автоматического запуска сервисов...${RESET}"; \
		make start-services || true; \
	fi

install-services-ubuntu: ## Установить и запустить необходимые сервисы на Ubuntu
	@echo "${GREEN}Установка необходимых сервисов для Ubuntu...${RESET}"
	@sudo apt-get update
	@if ! command -v rabbitmq-server >/dev/null 2>&1; then \
		echo "${YELLOW}Установка RabbitMQ...${RESET}"; \
		sudo apt-get install -y rabbitmq-server; \
	fi
	@if ! command -v redis-server >/dev/null 2>&1; then \
		echo "${YELLOW}Установка Redis...${RESET}"; \
		sudo apt-get install -y redis-server; \
	fi
	@if ! command -v postgresql >/dev/null 2>&1; then \
		echo "${YELLOW}Установка PostgreSQL...${RESET}"; \
		sudo apt-get install -y postgresql postgresql-contrib; \
	fi
	@echo "${GREEN}Запуск сервисов...${RESET}"
	@sudo systemctl enable --now rabbitmq-server 2>/dev/null || true
	@sudo systemctl enable --now redis-server 2>/dev/null || true
	@sudo systemctl enable --now postgresql 2>/dev/null || true
	@sleep 2
	@echo "${GREEN}✓ Сервисы установлены и запущены${RESET}"

start-services: ## Попытаться запустить зависимые сервисы автоматически
	@OS="$$(uname -s)"; \
	if [ "$$OS" = "Linux" ]; then \
		if command -v systemctl >/dev/null 2>&1; then \
			if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1 && ! nc -z localhost 5432 >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск PostgreSQL...${RESET}"; \
				sudo systemctl start postgresql 2>/dev/null || sudo systemctl start postgresql@* 2>/dev/null || true; \
				sleep 2; \
			fi; \
			if ! nc -z localhost 5672 >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск RabbitMQ...${RESET}"; \
				sudo systemctl start rabbitmq-server 2>/dev/null || true; \
				sleep 3; \
			fi; \
			if ! redis-cli ping >/dev/null 2>&1 && ! nc -z localhost 6379 >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск Redis...${RESET}"; \
				sudo systemctl start redis-server 2>/dev/null || sudo systemctl start redis 2>/dev/null || true; \
				sleep 2; \
			fi; \
		else \
			echo "${YELLOW}systemctl не найден. Запустите сервисы вручную.${RESET}"; \
		fi; \
	elif [ "$$OS" = "Darwin" ]; then \
		if command -v brew >/dev/null 2>&1; then \
			if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск PostgreSQL...${RESET}"; \
				brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null || true; \
			fi; \
			if ! nc -z localhost 5672 >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск RabbitMQ...${RESET}"; \
				brew services start rabbitmq 2>/dev/null || true; \
				sleep 3; \
			fi; \
			if ! redis-cli ping >/dev/null 2>&1; then \
				echo "${YELLOW}Запуск Redis...${RESET}"; \
				brew services start redis 2>/dev/null || true; \
				sleep 2; \
			fi; \
		else \
			echo "${YELLOW}Homebrew не найден. Запустите сервисы вручную.${RESET}"; \
		fi; \
	else \
		echo "${YELLOW}Неизвестная ОС: $$OS. Запустите сервисы вручную.${RESET}"; \
	fi

##@ Docker команды

build-docker: ## Собрать Docker образы
	@echo "${GREEN}Building Docker images...${RESET}"
	$(DOCKER_COMPOSE) build

up: ## Запустить все сервисы
	@echo "${GREEN}Starting services...${RESET}"
	$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}Services started!${RESET}"
	@echo "FastAPI: http://localhost:8000"
	@echo "RabbitMQ Management: http://localhost:15672 (guest/guest)"
	@echo "API Docs: http://localhost:8000/docs"

down: ## Остановить все сервисы
	@echo "${YELLOW}Stopping services...${RESET}"
	$(DOCKER_COMPOSE) down

restart: ## Перезапустить все сервисы
	@echo "${YELLOW}Restarting services...${RESET}"
	$(DOCKER_COMPOSE) restart

ps: ## Показать статус всех сервисов
	$(DOCKER_COMPOSE) ps

logs: ## Показать логи всех сервисов
	$(DOCKER_COMPOSE) logs -f

logs-app: ## Показать логи приложения
	$(DOCKER_COMPOSE) logs -f app

logs-celery: ## Показать логи Celery worker
	$(DOCKER_COMPOSE) logs -f celery

logs-db: ## Показать логи базы данных
	$(DOCKER_COMPOSE) logs -f postgres

##@ Управление сервисами

start-app: ## Запустить только FastAPI приложение
	$(DOCKER_COMPOSE) up -d app

stop-app: ## Остановить FastAPI приложение
	$(DOCKER_COMPOSE) stop app

start-celery: ## Запустить Celery worker
	$(DOCKER_COMPOSE) up -d celery

stop-celery: ## Остановить Celery worker
	$(DOCKER_COMPOSE) stop celery

restart-app: ## Перезапустить FastAPI приложение
	$(DOCKER_COMPOSE) restart app

restart-celery: ## Перезапустить Celery worker
	$(DOCKER_COMPOSE) restart celery

##@ Разработка

shell: ## Открыть shell в контейнере приложения
	$(DOCKER_COMPOSE) exec app bash

app-shell: shell ## Алиас для shell

celery-shell: ## Открыть shell в контейнере Celery
	$(DOCKER_COMPOSE) exec celery bash

##@ Очистка

clean: ## Остановить и удалить все контейнеры, сети и volumes
	@echo "${YELLOW}Cleaning up Docker resources...${RESET}"
	$(DOCKER_COMPOSE) down -v
	@echo "${GREEN}Cleanup complete!${RESET}"

clean-all: clean ## Полная очистка включая образы
	@echo "${YELLOW}Removing Docker images...${RESET}"
	docker rmi $$(docker images -q $(APP_NAME)*) 2>/dev/null || true
	@echo "${GREEN}Full cleanup complete!${RESET}"

##@ База данных

db-migrate: ## Запустить миграции БД (если используются)
	@echo "${GREEN}Running database migrations...${RESET}"
	$(DOCKER_COMPOSE) exec app python -c "from src.core.database.engine import db_helper; import asyncio; asyncio.run(db_helper.init_db())"

db-shell: ## Подключиться к PostgreSQL через psql
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d parser_kucoin

db-backup: ## Создать резервную копию базы данных
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres parser_kucoin > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "${GREEN}Backup created in backups/ directory${RESET}"

db-restore: ## Восстановить базу данных из резервной копии (использовать: make db-restore FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "${YELLOW}Usage: make db-restore FILE=path/to/backup.sql${RESET}"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec -T postgres psql -U postgres parser_kucoin < $(FILE)
	@echo "${GREEN}Database restored from $(FILE)${RESET}"

##@ Тестирование

test: ## Запустить тесты
	$(DOCKER_COMPOSE) exec app pytest

install: ## Установить зависимости локально (без Docker)
	@echo "${GREEN}Installing dependencies with Poetry...${RESET}"
	poetry install

##@ Мониторинг

health: ## Проверить статус здоровья всех сервисов
	@echo "${GREEN}Checking service health...${RESET}"
	@echo "FastAPI:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "${YELLOW}FastAPI not responding${RESET}"
	@echo "\nRabbitMQ:"
	@curl -s -u guest:guest http://localhost:15672/api/overview | python -m json.tool 2>/dev/null || echo "${YELLOW}RabbitMQ not responding${RESET}"
	@echo "\nPostgreSQL:"
	@$(DOCKER_COMPOSE) exec postgres pg_isready -U postgres && echo "${GREEN}PostgreSQL is ready${RESET}" || echo "${YELLOW}PostgreSQL not ready${RESET}"

check-fastapi: ## Проверить статус FastAPI и показать логи при ошибке
	@echo "${GREEN}Проверка статуса FastAPI...${RESET}"
	@if [ -f $(PID_FILE) ]; then \
		FASTAPI_PID=$$(head -1 $(PID_FILE) 2>/dev/null); \
		if [ -n "$$FASTAPI_PID" ]; then \
			if kill -0 $$FASTAPI_PID 2>/dev/null; then \
				echo "${GREEN}✓ FastAPI процесс запущен (PID: $$FASTAPI_PID)${RESET}"; \
			else \
				echo "${RED}✗ FastAPI процесс не найден (PID: $$FASTAPI_PID)${RESET}"; \
			fi; \
		fi; \
	else \
		echo "${YELLOW}⚠ PID файл не найден${RESET}"; \
	fi
	@if nc -z localhost 8000 >/dev/null 2>&1; then \
		echo "${GREEN}✓ Порт 8000 слушает${RESET}"; \
		echo "${GREEN}✓ FastAPI доступен на http://localhost:8000${RESET}"; \
	else \
		echo "${RED}✗ Порт 8000 не отвечает${RESET}"; \
		echo "${YELLOW}Последние строки из logs/fastapi.log:${RESET}"; \
		tail -30 logs/fastapi.log 2>/dev/null || echo "Лог файл не найден"; \
	fi

stats: ## Показать статистику использования ресурсов
	$(DOCKER_COMPOSE) stats

##@ Быстрые команды

dev: build-docker up logs ## Собрать, запустить и показать логи (для разработки)

rebuild: clean build-docker up ## Полная пересборка и запуск

.DEFAULT_GOAL := help

