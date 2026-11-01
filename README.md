# Vaurenith Backend

Backend-модуль проекта Vaurenith предоставляет HTTP API для работы с данными и инфраструктурой проекта. Приложение построено на FastAPI, использует PostgreSQL для хранения данных и Alembic для управления схемой базы данных.


## Запуск через Docker Compose

Требуются Docker и Docker Compose.

1. Создайте файл настроек из шаблона:

   ```bash
   cp .env.example .env
   ```

2. При необходимости измените параметры подключения и CORS в `.env`.
3. Запустите Backend и PostgreSQL:

   ```bash
   docker compose up --build
   ```

При старте контейнера Backend применяет миграции базы данных, затем запускает API на `http://localhost:8000`. Документация API доступна по адресу `http://localhost:8000/docs`.

Остановить сервисы можно командой `docker compose down`. Данные PostgreSQL сохраняются в Docker volume `postgres_data`.

## Локальный запуск

Требуются Python 3.13 и доступный сервер PostgreSQL.

1. Создайте и активируйте виртуальное окружение:

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

2. Установите зависимости для разработки и создайте конфигурацию:

   ```bash
   pip install -r requirements-dev.txt
   cp .env.example .env
   ```

3. В `.env` укажите параметры подключения к локальной базе PostgreSQL в `DATABASE_URL`. При необходимости скорректируйте `POSTGRES_DB`, `POSTGRES_USER` и `POSTGRES_PASSWORD` для настройки базы.
4. Примените миграции и запустите сервер:

   ```bash
   alembic upgrade head
   uvicorn app.main:app --app-dir src --reload
   ```

API будет доступно на `http://localhost:8000`, интерактивная документация — на `http://localhost:8000/docs`.

## Проверки качества

`requirements.txt` содержит только зависимости, необходимые для запуска сервиса. Docker-образ устанавливает этот список. `requirements-dev.txt` включает runtime-зависимости и инструменты для разработки, анализа кода и тестов. Semgrep подключён как pre-commit hook и устанавливается в отдельное окружение, поэтому его зависимости не конфликтуют с FastAPI.

Для локальной разработки установите dev-зависимости:

```bash
pip install -r requirements-dev.txt
```

Основные команды:

```bash
make lint
make lint-fix
make format
make format-check
make typecheck
make semgrep
make security
make test
make check
```

`make check` запускает линтер, проверку форматирования, Pyright, Bandit, Semgrep и тесты. При первом запуске pre-commit создаёт изолированное окружение Semgrep. Новые тесты размещаются в каталоге `tests` и запускаются командой `make test`.

## Настройки окружения

Основные переменные задаются в `.env`:

| Переменная | Назначение |
| --- | --- |
| `POSTGRES_DB` | Имя базы данных для Docker Compose |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `POSTGRES_PORT` | Порт PostgreSQL на хосте, по умолчанию `5432` |
| `DATABASE_URL` | SQLAlchemy URL подключения приложения к PostgreSQL |
| `CORS_ORIGINS` | Список разрешённых браузерных источников через запятую |
| `API_PREFIX` | Префикс маршрутов API, по умолчанию `/api/v1` |
| `LOG_LEVEL` | Уровень логирования, например `INFO` |
