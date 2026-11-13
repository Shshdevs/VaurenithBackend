# Vaurenith Backend

Backend-модуль проекта Vaurenith предоставляет HTTP API для работы с данными и инфраструктурой проекта. Приложение построено на FastAPI, использует PostgreSQL для хранения данных и Alembic для управления схемой базы данных.


## Запуск через Docker Compose

Требуются Docker и Docker Compose.

1. Создайте файл настроек из шаблона:

   ```bash
   cp .env.example .env
   ```

2. Заполните `.env`: задайте уникальный `POSTGRES_PASSWORD` и конфигурацию JWT от Vaurenith Identity Service. Укажите согласованные `AUTH_JWT_ISSUER` и `AUTH_JWT_AUDIENCE`, положите предоставленный issuer-ом public PEM ключ в `.local/keys/jwt-public.pem`, задайте `AUTH_JWT_PUBLIC_KEY_PATH`, clock skew и максимальное время жизни токена. Backend не выпускает JWT и не использует приватные ключи.
3. Запустите Backend и PostgreSQL:

   ```bash
   make docker
   ```

При старте контейнера Backend применяет миграции базы данных, затем запускает API на `http://localhost:8000`. Документация API доступна по адресу `http://localhost:8000/docs`. Порт PostgreSQL публикуется только на `127.0.0.1`.

`make docker-down` останавливает сервисы, сохраняя данные в Docker volume `postgres_data`. `make docker-logs` показывает логи, а `make docker-build` собирает образы без запуска.

## Локальная разработка

Требуются Python 3.13 и доступный сервер PostgreSQL.

1. Создайте виртуальное окружение, установите dev-зависимости и pre-commit hooks:

   ```bash
   make setup
   ```

   Цель создаёт `.env` из `.env.example`, только если `.env` ещё не существует.
2. Активируйте окружение:

   ```bash
   source .venv/bin/activate
   ```

3. Заполните `.env`: задайте `DATABASE_URL`, параметры подключения к PostgreSQL, JWT issuer/audience и путь `AUTH_JWT_PUBLIC_KEY_PATH` к файлу RSA public key. Значения issuer и audience должны быть выданы владельцем Identity Service.
4. Примените миграции и запустите сервер:

   ```bash
   make db-upgrade
   uvicorn app.main:app --app-dir src --reload
   ```

API будет доступно на `http://localhost:8000`, интерактивная документация — на `http://localhost:8000/docs`.

## Проверки качества

`requirements.txt` содержит только зависимости, необходимые для запуска сервиса. Docker-образ устанавливает этот список. `requirements-dev.txt` включает runtime-зависимости и инструменты для разработки, анализа кода и тестов. Semgrep подключён как pre-commit hook и устанавливается в отдельное окружение, поэтому его зависимости не конфликтуют с FastAPI.

Основные команды:

| Команда | Действие |
| --- | --- |
| `make test` | Запускает тесты из `TEST_PATH` (по умолчанию `tests`) |
| `make test TEST_PATH=tests/unit/domain/identity` | Запускает выбранный каталог тестов |
| `make test PYTEST_ARGS="-k create_user -x"` | Передаёт дополнительные аргументы pytest |
| `make test-unit` | Запускает unit-тесты |
| `make test-integration` | Запускает интеграционные тесты, загружая `TEST_DATABASE_URL` из окружения или `.env` |
| `make test-cov` | Запускает тесты с отчётом покрытия для пакета `app` |
| `make lint` / `make format-check` / `make typecheck` | Проверяет стиль, форматирование и типы |
| `make architecture` | Проверяет границы пакетов и разрешённые зависимости между слоями |
| `make fix` | Исправляет lint-ошибки и форматирует файлы |
| `make security` | Запускает Bandit и Semgrep |
| `make check` | Запускает проверки стиля, типов, архитектуры, безопасности и все тесты |
| `make db-upgrade` / `make db-current` | Применяет миграции к `DATABASE_URL` / показывает текущую ревизию |
| `make db-upgrade-test` | Применяет миграции к отдельной БД из `TEST_DATABASE_URL`; откажется, если URL указывает на основную БД |
| `make db-revision MESSAGE="add table"` | Создаёт автогенерируемую миграцию |
| `make docker` / `make docker-down` | Запускает локальный Compose-стек / останавливает его без удаления данных |
| `make docker-build` / `make docker-logs` | Собирает образы / показывает логи сервисов |

Для сквозной проверки JWT и Session подготовьте отдельную PostgreSQL базу в `TEST_DATABASE_URL` и запустите `RUN_JWT_SESSION_SMOKE=1 .venv/bin/pytest tests/integration/api/test_jwt_session_smoke.py`. Smoke-тест применит миграции к тестовой БД, создаст пользователя с тестовым JWT, проверит HTTP 200 на `/users/me` и негативные JWT сценарии. Тестовый пользователь и Session останутся в указанной тестовой БД. RSA private key и JWT не записываются в репозиторий или файлы; временный public key PEM удаляется по завершении. Без флага smoke-тест будет пропущен обычным pytest запуском.

`make check` запускает линтер, проверку форматирования, Pyright, Bandit, Semgrep и тесты. При первом запуске pre-commit создаёт изолированное окружение Semgrep.

## Сообщения коммитов

Commit-msg hook проверяет сообщения перед созданием коммита, в том числе при использовании `gcmsg`. Формат заголовка:

```text
<type>(<scope>): <short imperative summary>
```

Допустимые типы: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `ci`, `perf`, `style`, `revert`. Scope обязателен, пишется строчными буквами и может содержать цифры и дефисы. Краткое описание пишется по-английски в повелительной форме, без точки в конце.

Примеры: `feat(identity): add user registration endpoint`, `test(identity): cover user repository persistence`, `chore(dev): automate local development workflows`.

`make setup` устанавливает commit-msg hook автоматически. В существующем окружении hooks можно установить или обновить командой `make install-hooks`.

Интеграционный тест SQLAlchemy-репозитория требует отдельную PostgreSQL-базу в `TEST_DATABASE_URL` и применённые к ней миграции. Укажите URL тестовой БД в `.env` или экспортируйте его в окружение. Перед миграцией `make db-upgrade-test` сравнивает адрес, порт, имя базы и драйвер с `DATABASE_URL` и отказывается работать, если они совпадают. Сам тест также проверяет, что тестовая база отдельная, и откатывает тестовую транзакцию.

GitHub Actions поднимает отдельный PostgreSQL-сервис, применяет к нему миграции и запускает интеграционные тесты вместе с остальными проверками.

```bash
make db-upgrade-test
make test-integration
```

## Настройки окружения

Основные переменные задаются в `.env`:

| Переменная | Назначение |
| --- | --- |
| `POSTGRES_DB` | Имя базы данных для Docker Compose |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `POSTGRES_PORT` | Порт PostgreSQL на `127.0.0.1`, по умолчанию `5432` |
| `DATABASE_URL` | SQLAlchemy URL подключения приложения к PostgreSQL при локальном запуске без Compose |
| `AUTH_JWT_ISSUER` | Точный issuer собственного Vaurenith Identity Service; обязателен |
| `AUTH_JWT_AUDIENCE` | Единственная audience для VaurenithBackend; обязателен |
| `AUTH_JWT_PUBLIC_KEY_PATH` | Путь к доверенному RSA public PEM ключу для RS256; по умолчанию `.local/keys/jwt-public.pem` |
| `AUTH_JWT_CLOCK_SKEW_SECONDS` | Допустимый временной skew в секундах, от 0 до 60 |
| `AUTH_JWT_MAX_LIFETIME_SECONDS` | Максимальная длительность access token в секундах |
| `CORS_ORIGINS` | Список разрешённых браузерных источников через запятую |
| `API_PREFIX` | Префикс маршрутов API, по умолчанию `/api/v1` |
| `LOG_LEVEL` | Уровень логирования, например `INFO` |

JWT для identity-маршрутов должен соответствовать contract `at+jwt` / RS256, содержать `iss`, `aud`, `sub` (неизменяемый UUID внутреннего пользователя), `exp`, `iat`, `nbf`, `jti`, `email` и `auth_provider`. `/users/me` также требует активную Backend Session, содержащую SHA-256 хеш полного токена. `POST /users/create` принимает полностью проверенный JWT без существующей Session и создаёт пользователя вместе с первой Session атомарно.

## Экосистема Vaurenith

- [VaurenithBackend](https://github.com/Shshdevs/VaurenithAuth) — cервис аутентификации и управления пользовательскими сессиями.
- [VaurenithClient](https://github.com/Shshdevs/VaurenithClient) — клиентское приложение.

