# Реализованные API-контракты

Документ описывает контракты, подключённые в `src/app`. Источник фактического префикса — настройка `API_PREFIX` (`api_prefix`); поэтому ниже пути приведены относительно него. Все тела и ответы используют JSON, UUID сериализуются строками, даты/время — ISO 8601. Pydantic-схемы запрещают дополнительные поля (`extra="forbid"`). Для изменяющих запросов `PUT` требуется полный набор полей схемы; `PATCH` применяется только для специализированных полей статуса. Большинство предметных маршрутов требует Bearer-аутентификацию с действующей Session. Исключения: `/health`, `/health/ready`, `/users/create`, `POST /users/me/devices` и `POST /users/me/devices/{device_id}/sessions`; последние маршруты требуют проверенный issuer JWT, но не предварительно зарегистрированную Session для этого же JWT.

## Общий формат

Успешные ответы обёрнуты в объект:

```json
{"status":"200 OK","code":"UPDATED","entity_type":"project","data":{}}
```

`status` — строка `"<код> <фраза HTTP>"`. `code` — стабильный enum для локализации, `entity_type` — тип сущности или `null` для общих операций. `data` и `details` могут быть `null`. Коллекции возвращаются в `data` как массив, в том числе пустой. Удаления обычно отвечают `200 OK` с `data: null`. Создание отвечает `201 Created`. В проекте нет общей пагинации; единственный лимитный список — журнал изменений.

Коды успешных ответов: `CREATED`, `UPDATED`, `STATUS_UPDATED`, `DELETED`, `RETRIEVED`, `RECORDED`, `ADDED`, `REMOVED`, `CACHED`, `LOGGED_OUT`, `SYNCED`, `OK`. Для действий над сущностями используется значение `entity_type` из доменного enum `EntityType` (строчные snake_case значения), включая `client_device` и `session`. `SYNCED` обозначает завершённую синхронизацию, тогда как текущее состояние синхронизации по-прежнему находится в `SyncStatus`.

Ошибки имеют тот же конверт, обычно без `data`:

```json
{"status":"422 Unprocessable Entity","code":"VALIDATION_ERROR","entity_type":null,"data":[...]}
```

| HTTP | Условие | Тело / поведение |
|---|---|---|
| 400–599 от HTTP-исключения | HTTP ошибка | `HTTP_ERROR` либо специализированный код; исходный `detail` в `details` |
| 401 Unauthorized | отсутствует/не прошла аутентификация или авторизация | `UNAUTHORIZED`, `details` исключения, заголовок `WWW-Authenticate: Bearer` |
| 403 Forbidden | доступ запрещён | `FORBIDDEN`, `details` исключения |
| 404 Not Found | сущность не найдена/недоступна | `NOT_FOUND`, тип сущности выводится для предметных исключений, исходное сообщение в `details` |
| 409 Conflict | конфликт, включая конфликт версии | `CONFLICT`, тип сущности выводится для предметных исключений, подробность в `details` |
| 410 Gone | курсор change log уже истёк | `RESYNC_REQUIRED`, `entity_type: "change_log"`, `data: {"resync_required":true,"restart_sequence":N}` |
| 422 Unprocessable Entity | ошибка схемы или InvalidInput | `VALIDATION_ERROR` или `INVALID_INPUT`; ошибки Pydantic в `data` содержат только `loc`, `type` и `msg`. Поля `input`, `ctx` и остальные внутренние данные валидации не возвращаются. Текст предметной ошибки в `details` |
| 500 Internal Server Error | необработанная ошибка | `INTERNAL_ERROR`, детали не раскрываются |

Валидация пути/query/body автоматически может возвращать 422. Каждому ответу middleware добавляет `X-Request-ID`, `X-Process-Time-Ms`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. Время обработки — миллисекунды в виде строки. CORS задаётся конфигурацией.

## Health

| Метод и путь | Доступ | Успех |
|---|---|---|
| `GET /health` | публичный | `200`; `data: {status:"OK", timestamp}` |
| `GET /health/ready` | публичный | `200`; `{status:"OK", timestamp, database:{status:"OK", message:"Database is ready"}}`; если БД недоступна — `503`, верхний статус `UNAVAILABLE`, сообщение `Service unavailable`, database `{status:"UNAVAILABLE",message:"Database connection failed"}` |

## Identity

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /users/create` | `email`, `device_name`, `platform`; опционально `display_name`, `app_version` | `201`, пользователь |
| `GET /users/me` | — | `200`, текущий пользователь |
| `POST /users/logout` | — | `200`, `data:null`, отзывает текущую сессию |
| `DELETE /users/me` | — | `200`, `data:null`, удаляет текущего пользователя |

`UserCreateRequest`: email должен быть валидным; `device_name` после trim непустой, длина 1–255; `display_name` до 255 символов; `app_version` до 50. `platform`: `macos`, `windows`, `linux`, `ios`, `android`, `other`. `UserData`: `id`, `email`, `display_name`, `nickname`, `auth_provider`, `created_at`, `updated_at`.

### ClientDevice и Session

Управление устройствами owner-scoped по `VerifiedIdentity.user_id`. Новая регистрация и создание Session по новому issuer JWT проверяют подпись/claims, но не требуют уже активной Session для этого JWT. Все остальные маршруты требуют JWT с действующей Session, ACTIVE ClientDevice и согласованным владельцем. Текущая `/users/create` по-прежнему создаёт первую ClientDevice и связанную Session.

| Метод и путь | Тело / параметры | Ответ и поведение |
|---|---|---|
| `POST /users/me/devices` | `name`, `platform`, опционально `app_version` | `201 ClientDeviceData`; сервер назначает ID, одновременно создаёт linked Session |
| `GET /users/me/devices` | — | список устройств текущего пользователя |
| `GET /users/me/devices/{device_id}` | — | устройство владельца; чужой/несуществующий ID даёт owner-safe `404` |
| `PATCH /users/me/devices/{device_id}` | `name?`, `app_version?`; null `app_version` очищает версию | обновлённый `ClientDeviceData`; требуется хотя бы одно поле |
| `POST /users/me/devices/{device_id}/sessions` | пустое тело | `201 SessionData`; создаёт новую Session по новому JWT для ранее зарегистрированного ACTIVE устройства |
| `GET /users/me/devices/{device_id}/sessions` | — | список `SessionData` без JWT и token hash |
| `PATCH /users/me/devices/{device_id}/status` | `status`: `active` или `inactive` | обновлённый `ClientDeviceData`; переход в INACTIVE отзывает действующие сессии |
| `DELETE /users/me/devices/{device_id}` | — | `200`, `data:null`; терминальный REVOKED и отзыв активных сессий устройства |

`ClientDeviceRegisterRequest`: `name` после trim непустой, 1–255 символов; `platform`: `macos`, `windows`, `linux`, `ios`, `android`, `other`; `app_version` до 50 символов. DTO запрещают owner ID, статус и системные поля. Валидный новый JWT issuer-а достаточен для JWT-only enrollment; после компрометации account JWT можно зарегистрировать ещё одно устройство, поэтому этот механизм не заменяет step-up/approval.

`ClientDeviceData`: `id`, `name`, `platform`, `app_version`, `status`, `registered_at`, `last_seen_at`, `revoked_at`. `SessionData`: `id`, `client_device_id`, `created_at`, `expires_at`, `revoked_at`. Статусы: ACTIVE принимает запросы и новые сессии; INACTIVE запрещает их и отзывает все активные Session; ACTIVE можно восстановить, но старые JWT не оживают; REVOKED терминален, повторная регистрация выдаёт новый ID. Существующий `POST /users/logout` по-прежнему отзывает только Session текущего JWT.

Отзыв действует после commit на все последующие auth checks связанных сессий и не ждёт JWT expiry. Уже выполняющиеся запросы он не отменяет. ClientDevice ID не является криптографическим доказательством физического устройства; скопированный действующий bearer JWT остаётся bearer credential до отзыва его Session/device или expiry.

## Projects и окружения

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /projects` | `name`, опционально `project_type` (по умолчанию `other`), `version` (1), `description`, `metadata` | `201 ProjectData` |
| `GET /projects` | — | список проектов пользователя |
| `GET /projects/{project_id}` | — | проект |
| `PUT /projects/{project_id}` | `name`, `project_type`, `status`, `version`, опционально `description`, `metadata` | обновлённый проект; `version` — ожидаемая версия |
| `DELETE /projects/{project_id}` | — | `200`, `data:null` |
| `POST /projects/{project_id}/environments` | `name`, опционально `environment_type` (`other`), `description`, `configuration`, `version` (1) | `201 EnvironmentData` |
| `GET /projects/{project_id}/environments` | — | список окружений проекта |
| `GET /projects/{project_id}/environments/{environment_id}` | — | окружение, принадлежащее указанному проекту |
| `PUT /projects/{project_id}/environments/{environment_id}` | `name`, `environment_type`, `version`, опционально `description`, `configuration` | обновлённое окружение; версия ожидаемая |
| `DELETE /projects/{project_id}/environments/{environment_id}` | — | `200`, `data:null` |

`ProjectData`: `id`, `user_id`, `name`, `slug`, `description`, `project_type`, `status`, `metadata`, `version`, `created_at`, `updated_at`, `deleted_at`. Типы проекта: `software`, `infrastructure`, `fullstack`, `other`; статусы: `active`, `archived`. `EnvironmentData`: `id`, `project_id`, `name`, `slug`, `environment_type`, `description`, `configuration`, `version`, временные метки и `deleted_at`. Типы: `development`, `testing`, `staging`, `production`, `local`, `other`.

## Репозитории разработки

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `POST /projects/{project_id}/repositories` | `name`; опциональны `repository_type`, `description`, `remote_url`, `default_branch` | `201 RepositoryData`; проект должен принадлежать пользователю |
| `GET /projects/{project_id}/repositories` | — | активные репозитории проекта |
| `GET /repositories` | — | активные репозитории пользователя |
| `GET /repositories/{repository_id}` | — | репозиторий, если проект принадлежит пользователю |
| `PUT /repositories/{repository_id}` | `version`, `name`, `repository_type`; остальные поля метаданных опциональны | обновлённый `RepositoryData`, версия увеличивается на 1 |
| `DELETE /repositories/{repository_id}?expected_version={version}` | — | `200`, `data:null`; репозиторий мягко удаляется |

`RepositoryData`: `id`, `project_id`, `name`, `slug`, `description`, `remote_url`, `default_branch`, `repository_type`, `version`, `created_at`, `updated_at`, `deleted_at`. Тип: `git` или `other`. Изменения попадают в ChangeLog без `remote_url` и `description`.

## Связи проекта и устройства

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /project_devices` | `project_id`, `device_id`, опционально `role` | `201 ProjectDeviceData` |
| `GET /project_devices/{project_device_id}` | — | связь |
| `GET /projects/{project_id}/devices` | — | связи устройств с проектом |
| `GET /devices/{device_id}/projects` | — | связи проекта с устройством |
| `PUT /project_devices/{project_device_id}` | `version`, `project_id`, `device_id`, опционально `role` | обновлённая связь; `version` — ожидаемая версия, при конфликте возвращается 409 |
| `DELETE /project_devices/{project_device_id}` | — | `200`, `data:null` |

`ProjectDeviceData`: `id`, `project_id`, `device_id`, `role`, `created_at`, `version`. Роль должна соответствовать доменному `ProjectDeviceRole`.

## Связи сущностей

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `POST /projects/{project_id}/relations` | `source_entity_type`, `source_entity_id`, `target_entity_type`, `target_entity_id`, `relation_type`; опциональны `confidence`, `metadata` | `201 RelationData`; проект и ссылки проверяются по владельцу и принадлежности проекту |
| `GET /projects/{project_id}/relations` | опционально `entity_type` и `entity_id` вместе | связи проекта; при фильтре возвращаются совпадения по исходному или целевому объекту |
| `GET /projects/{project_id}/relations/{relation_id}` | — | связь |
| `PUT /projects/{project_id}/relations/{relation_id}` | те же поля, что при создании | обновлённая связь; `origin` остаётся неизменным |
| `DELETE /projects/{project_id}/relations/{relation_id}` | — | `200`, `data:null` |

`RelationData`: `id`, `project_id`, тип и UUID исходного объекта, тип и UUID целевого объекта, `relation_type`, `origin`, `confidence`, `metadata`, `created_at`, `updated_at`. Новые связи создаются с `origin=user_defined`. Доверие — число от 0 до 1 включительно с точностью до 4 десятичных знаков. `OTHER` допускает внешние UUID-ссылки без проверки внутренней таблицы; ссылки на известные типы ограничены текущим пользователем и указанным проектом.

## Инфраструктура

### Устройства

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /devices` | `name`, `device_type`; опционально `hostname`, `description`, `operating_system`, `os_version`, `architecture`, `tags` | `201 Device` |
| `GET /devices` | — | устройства пользователя |
| `GET /devices/{device_id}` | — | устройство |
| `PUT /devices/{device_id}` | `version`, `name`, `device_type`, те же опциональные поля | обновлённое устройство |
| `DELETE /devices/{device_id}` | — | `200`, `data:null` |

`Device`: `id`, `user_id`, `name`, `slug`, hostname/description, `device_type`, ОС и версия, архитектура, `tags`, `last_seen_at`, `last_status_at`, `version`, `created_at`, `updated_at`, `deleted_at`. Тип: `physical`, `virtual`, `vps`, `cloud`, `other`.

### Группы устройств

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /device-groups` | `name`, опционально `description` | `201 DeviceGroup` |
| `GET /device-groups` | — | список групп устройств пользователя |
| `GET /device-groups/{device_group_id}` | — | группа |
| `GET /device-groups/{device_group_id}/members` | — | участники группы (ID записей членства и устройств) |
| `POST /device-groups/{device_group_id}/members` | `device_id` | `201 DeviceGroupMemberData`; устройство добавлено в группу |
| `DELETE /device-groups/{device_group_id}/members/{device_id}` | — | `200`, `data:null`; устройство удалено из группы |
| `PUT /device-groups/{device_group_id}` | `version`, `name`, опционально `description` | группа; `version` — ожидаемая версия, при конфликте возвращается 409 |
| `DELETE /device-groups/{device_group_id}` | — | `200`, `data:null` |

`DeviceGroup`: `id`, `user_id`, `name`, `slug`, `description`, `created_at`, `updated_at`, `version`.
`DeviceGroupMemberData`: `id`, `group_id`, `device_id`, `created_at`. И группа, и устройство должны принадлежать текущему пользователю. Повторное добавление участника возвращает 409; удаление отсутствующего участника — 404. Добавление и удаление записываются в ChangeLog как `device_group_member`.

### Подключения

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /connections` | `device_id`, `name`, `host`, `username`, `authentication_type`; `port`=22, `connection_timeout`=30, `is_default`=false по умолчанию | `201 ConnectionData` |
| `GET /connections` | — | подключения пользователя |
| `GET /connections/{connection_id}` | — | подключение |
| `GET /devices/{device_id}/connections` | — | подключения устройства |
| `PUT /connections/{connection_id}` | `version`, `name`, `host`, `port`, `username`, `authentication_type`, `connection_timeout`, `is_default` | подключение |
| `PATCH /connections/{connection_id}/status` | `version`, `status`; опционально `last_connected_at`, `last_error` | подключение с обновлённым статусом |
| `DELETE /connections/{connection_id}` | — | `200`, `data:null` |

`ConnectionData`: `id`, `device_id`, `name`, `slug`, `host`, `port`, `username`, `authentication_type`, `connection_timeout`, `is_default`, `last_connected_at`, `last_status`, `version`, `created_at`, `updated_at`. Тип аутентификации: `password`, `ssh_key`, `agent`, `other`; состояние: `connected`, `disconnected`, `failed`, `unknown`. Порт 1–65535, timeout > 0, `last_error` до 4000 символов.

### Сервисы

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /services` | `device_id`, `name`, `service_type`; опционально `project_id`, `environment_id`, `description`, `system_identifier`, `metadata` | `201 ServiceData` |
| `GET /services` | — | сервисы пользователя |
| `GET /services/{service_id}` | — | сервис |
| `GET /devices/{device_id}/services` | — | сервисы устройства |
| `GET /projects/{project_id}/services` | — | сервисы проекта |
| `GET /environments/{environment_id}/services` | — | сервисы окружения |
| `PUT /services/{service_id}` | `version`, `device_id`, `name`, `service_type`; опционально `project_id`, `environment_id`, `description`, `system_identifier`, `metadata` | сервис |
| `PATCH /services/{service_id}/status` | `version`, `status` | сервис с обновлённым статусом |
| `DELETE /services/{service_id}` | — | `200`, `data:null` |

`ServiceData`: `id`, `project_id`, `environment_id`, `device_id`, `name`, `slug`, `service_type`, `description`, `system_identifier`, `status`, `last_status_at`, `metadata`, `version`, `created_at`, `updated_at`. `service_type`: `systemd`, `docker`, `application`, `database`, `web_server`, `other`; статус ресурса: `running`, `stopped`, `restarting`, `paused`, `failed`, `unknown`.

### Контейнеры

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /containers` | обязательны `device_id`, `container_runtime_id`, `name`; остальные поля необязательны: `project_id`, `environment_id`, `service_id`, `image`, `status` (`unknown`), `ports`, `volumes`, `networks`, `started_at`, `last_seen_at`, `metadata` | `201 ContainerData` |
| `GET /containers` | — | контейнеры пользователя |
| `GET /containers/{container_id}` | — | контейнер |
| `GET /devices/{device_id}/containers` | — | по устройству |
| `GET /projects/{project_id}/containers` | — | по проекту |
| `GET /environments/{environment_id}/containers` | — | по окружению |
| `GET /services/{service_id}/containers` | — | по сервису |
| `PUT /containers/{container_id}` | `version`, `device_id`, `container_runtime_id`, `name`, `status`; остальные поля создания необязательны | контейнер |
| `DELETE /containers/{container_id}` | — | `200`, `data:null` |

`ContainerData`: `id`, project/environment/device/service IDs, `container_runtime_id`, `name`, `slug`, `image`, `status`, `ports`, `volumes`, `networks`, `started_at`, `last_seen_at`, `metadata`, `version`, временные метки. Статус: `created`, `running`, `paused`, `restarting`, `exited`, `dead`, `unknown`.

### Базы данных

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /databases` | обязательны `device_id`, `name`, `dbms_type`; остальные поля опциональны: project/environment/container/service IDs, `host`, `port`, `database_name`, `status` (`unknown`), `last_checked_at`, `metadata` | `201 DatabaseData` |
| `GET /databases` | — | базы пользователя |
| `GET /databases/{database_id}` | — | база |
| `GET /devices/{device_id}/databases` | — | по устройству |
| `GET /projects/{project_id}/databases` | — | по проекту |
| `GET /environments/{environment_id}/databases` | — | по окружению |
| `GET /containers/{container_id}/databases` | — | по контейнеру |
| `GET /services/{service_id}/databases` | — | по сервису |
| `PUT /databases/{database_id}` | `version`, `device_id`, `name`, `dbms_type`, `status`; остальные поля создания опциональны | база |
| `DELETE /databases/{database_id}` | — | `200`, `data:null` |

`DatabaseData`: `id`, project/environment/device/container/service IDs, `name`, `slug`, `dbms_type`, `host`, `port`, `database_name`, `status`, `last_checked_at`, `metadata`, `version`, временные метки. `dbms_type`: `postgresql`, `mysql`, `mariadb`, `mongodb`, `redis`, `sqlite`, `other`; `status` — перечисление `ResourceStatus` выше. Порт 1–65535.

## Мониторинг

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `POST /events` | `event_type`, `result`, `created_at`; необязательны `project_id`, `device_id`, `client_device_id`, `description`, `metadata` | `201 EventData`; ссылки на проект, устройство и клиентское устройство проверяются по владельцу |
| `GET /events` | query фильтры `project_id`, `device_id`, `event_type`, `result`, `start`, `end`; `limit` (100, 1–500), `offset` (0) | события пользователя по убыванию времени создания |
| `POST /logs/metadata` | обязательно `source`; опциональны `project_id`, `device_id`, `service_id`, `container_id`, `reference`, `description`, `severity`, `records_count`, `collected_at` | `201 LogMetadataData`; все связанные объекты проверяются по владельцу и согласованности связей |
| `GET /logs/metadata` | query фильтры `project_id`, `device_id`, `service_id`, `container_id`, `source`, `severity`, `start`, `end`; `limit` (100, 1–500), `offset` (0) | метаданные логов текущего пользователя по времени сбора |
| `POST /devices/{device_id}/metrics` | `metric_type`, `value`, `unit`, `collected_at`; опционально `source` | `201 MetricData`; устройство должно принадлежать пользователю |
| `GET /devices/{device_id}/metrics` | query `start`, `end` (интервал `[start, end)`), `limit` (100, 1–500), `offset` (0) | метрики устройства по убыванию времени сбора |

`MetricData`: `id`, `device_id`, `metric_type`, `value`, `unit`, `source`, `collected_at`. Значение — неотрицательное число с точностью до 6 десятичных знаков; время должно содержать часовой пояс. Диапазон может быть открыт с любой стороны, но если указаны обе границы, `start` должен предшествовать `end`. `LogMetadata` содержит только указатель и описательные поля: содержимое логов в API не передаётся и не сохраняется. `description` должна быть кратким безопасным описанием без строк лога, токенов, паролей и других секретов; `reference` — непрозрачный указатель, а не содержимое лога. Временной диапазон фильтрует `collected_at` как полуоткрытый интервал `[start, end)`. Метаданные логов, метрики и события не записываются в ChangeLog как отдельные события. В metadata событий запрещены ключи, похожие на имена секретных данных (password, secret, token, credential, authorization, private key, API key).

## Настройки

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `GET /settings?scope=global` | — | глобальные настройки пользователя |
| `GET /settings?scope=client&client_device_id={uuid}` | — | настройки принадлежащего пользователю клиентского устройства |
| `GET /settings/{setting_id}` | — | настройка пользователя |
| `POST /settings` | `scope`, `key`, `value`; для `client` обязателен `client_device_id` | `201 SettingData` |
| `PUT /settings/{setting_id}` | `expected_version`, `value` | обновлённая `SettingData`, версия увеличивается на 1 |
| `DELETE /settings/{setting_id}?expected_version={version}` | — | `200`, `data:null` |

`SettingData`: `id`, `user_id`, `client_device_id`, `scope`, `key`, `value`, `version`, `created_at`, `updated_at`. `scope`: `global` или `client`. Ключ уникален в области видимости. Изменения записываются в ChangeLog; payload содержит область, ключ и ID устройства, но не значение настройки. Для snapshot global scope читается через `GET /settings?scope=global`, client scope — через запрос с известным `client_device_id`. Отдельного API для перечисления всех ClientDevice ID нет, поэтому полный обход client-scoped настроек всех устройств аккаунта существующими маршрутами не гарантирован.

## Автоматизация

Все маршруты требуют Bearer-аутентификацию. Скрипты принадлежат пользователю; привязка к проекту необязательна и проверяется по владельцу проекта. Backend хранит скрипты и очередь заданий, но исполняет код клиентский агент.

| Метод и путь | Тело / параметры | Ответ и поведение |
|---|---|---|
| `POST /scripts` | `name`, `content`, `execution_type`; опционально `project_id`, `description`, `interpreter`, `parameters`, `risk_level`, `requires_confirmation` | `201 ScriptData` |
| `GET /scripts` | — | список активных скриптов пользователя |
| `GET /scripts/{script_id}` | — | скрипт владельца |
| `PUT /scripts/{script_id}` | как создание и обязательный `version` | обновлённый скрипт, версия увеличивается; при конфликте версии — 409 |
| `DELETE /scripts/{script_id}?expected_version={version}` | — | мягкое удаление; конфликт версии — 409 |
| `GET /scripts/{script_id}/targets` | — | назначения скрипта на устройства |
| `POST /scripts/{script_id}/targets` | `device_id`; опционально `environment_id` | `201 ScriptTargetData`; устройство и окружение должны принадлежать пользователю; повтор назначения — 409 |
| `DELETE /scripts/{script_id}/targets/{target_id}` | — | удаляет назначение |
| `POST /scripts/{script_id}/executions` | `client_device_id`; опционально `device_id`, `parameters`, `idempotency_key`, `confirmed` | `201 ScriptExecutionData`, задание `pending`; SSH-устройство должно быть назначено скрипту |
| `GET /script-executions/pending?client_device_id={uuid}` | — | ожидающие задания с данными скрипта для клиентского агента |
| `POST /script-executions/{execution_id}/start` | `client_device_id` | переводит принадлежащее этому клиенту задание из `pending` в `running` |
| `PUT /script-executions/{execution_id}/result` | `client_device_id`, конечный `status`; опционально `exit_code`, `error_message`, `sanitized_output_summary` | фиксирует результат; полный вывод команды backend не хранит |
| `GET /script-executions?script_id={uuid}` | фильтр необязателен | история выполнений пользователя |
| `GET /script-executions/{execution_id}` | — | выполнение владельца |

`ScriptData` включает содержимое скрипта. Script CRUD API и очередь выполнения продолжают возвращать актуальные данные согласно своим авторизованным контрактам. Для новых ChangeLog-событий `script` операции `insert` и `update` включают только `project_id`, `execution_type`, `risk_level` и `requires_confirmation`; событие `delete` является tombstone и имеет `payload: null`. Содержимое, параметры, имя, описание, interpreter и любые другие поля Script в новых ChangeLog payload не включаются. Версия, sequence и общий формат ChangeLog не меняются. Опасные уровни требуют `requires_confirmation=true`; если это поле включено, создание выполнения дополнительно требует `confirmed=true`. Результат передаётся клиентом только в сокращённом очищенном виде. Ключ идемпотентности обеспечивает повтор запроса без создания второго выполнения.

## Синхронизация

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `GET /change-logs` | query `after_sequence` (по умолчанию 0, ≥0), `limit` (100, 1–100) | массив `ChangeLogData`; изменения текущего пользователя после указанной последовательности |
| `POST /sync-state` | `client_device_id`, `status`; опционально `entity_type`, `entity_id`, `local_version`, `server_version` | `201 SyncStateData` |
| `GET /sync-state/{sync_state_id}` | — | состояние синхронизации |
| `PUT /sync-state/{sync_state_id}` | `expected_version`, `server_version`, `status`, `last_error` | обновлённое состояние |
| `PATCH /sync-state/{sync_state_id}/status` | `status` | состояние с новым статусом |
| `DELETE /sync-state/{sync_state_id}` | — | `200`, `data:null` |

`SyncStateData`: `id`, `user_id`, `client_device_id`, `updated_at`, `version`, `entity_type`, `entity_id`, `local_version`, `server_version`, `sync_status`, `last_synced_at`, `last_error`. Версии неотрицательные; для create/update верхняя граница — `2^63−1`, а `expected_version` — `2^63−2`. Статусы: `synced`, `pending`, `syncing`, `conflict`, `failed`, `offline`.

`ChangeLogData`: `id`, `user_id`, `entity_type`, `entity_id`, `operation`, `version`, `sequence`, `changed_by_client_id`, `changed_by_user_id`, `payload`, `created_at`. Операция: `insert`, `update`, `delete`. `EntityType` включает `user`, `client_device`, `session`, `project`, `environment`, `project_device`, `device`, `device_group`, `device_group_member`, `connection`, `service`, `container`, `database`, `repository`, `branch`, `commit`, `code_component`, `dependency`, `script`, `script_execution`, `script_target`, `relation`, `event`, `log_metadata`, `change_log`, `metric`, `settings`, `sync_state`, `other`.

Перечень `EntityType` шире типов с активными ChangeLog producers и не является sync registry. Registry типов с producer, полями payload и owner-scoped API для загрузки полного текущего состояния, а также протокол snapshot после 410 описаны в [client-sync-requirements.md](client-sync-requirements.md). Snapshot собирается клиентом из перечисленных GET API; отдельного серверного snapshot endpoint нет. `sync_state` в текущем backend записывает CRUD/status события в ChangeLog, но list endpoint для полного snapshot отсутствует. Его участие в пользовательской ленте синхронизации остаётся отдельным архитектурным решением, а восстановление SyncState из snapshot не гарантируется.

## Примечания к контракту

- UUID-параметры пути должны быть корректными UUID; иначе FastAPI вернёт 422.
- Ошибки предметной области `NotFound`, `InvalidInput`, `Conflict`, `Unauthorized` отображаются в 404/422/409/401 соответственно. Текст зависит от конкретного use case и не фиксирован этим документом.
- Запросы с неизвестными полями отклоняются. Для nullable полей отсутствие и `null` могут совпадать; отдельные PATCH-операции статуса перечислены выше.
- В API сейчас подключены только перечисленные маршруты. Наличие доменных сущностей в других модулях само по себе не означает наличие HTTP endpoint.

## Development code components

- `POST /v1/repositories/{repository_id}/code-components` creates structural metadata for a code component.
- `GET /v1/repositories/{repository_id}/code-components` lists components in an owned repository.
- `GET /v1/code-components/{component_id}` returns a code component.
- `PUT /v1/code-components/{component_id}` updates component metadata with an expected `version`.
- `DELETE /v1/code-components/{component_id}?expected_version={version}` deletes an unreferenced code component.
