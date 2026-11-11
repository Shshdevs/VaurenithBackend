# Реализованные API-контракты

Документ описывает контракты, подключённые в `src/app` на момент проверки. Источник фактического префикса — настройка `API_PREFIX` (`api_prefix`); поэтому ниже пути приведены относительно него. Все тела и ответы используют JSON, UUID сериализуются строками, даты/время — ISO 8601. Pydantic-схемы запрещают дополнительные поля (`extra="forbid"`). Для изменяющих запросов `PUT` требуется полный набор полей схемы; `PATCH` применяется только для специализированных полей статуса. Большинство предметных маршрутов требует проверенную Bearer-аутентификацию. Исключения: `/health`, `/health/ready`, `/users/create` (для него нужна проверенная идентичность клиента, но не существующий пользователь).

## Общий формат

Успешные ответы обёрнуты в объект:

```json
{"status":"200 OK","message":"...","data":{}}
```

`status` — строка `"<код> <фраза HTTP>"`; `message` и `data` могут быть `null`. Коллекции возвращаются в `data` как массив, в том числе пустой. Удаления обычно отвечают `200 OK` с `data: null`. Создание отвечает `201 Created`. В проекте нет общей пагинации; единственный лимитный список — журнал изменений.

Ошибки имеют тот же конверт, обычно без `data`:

```json
{"status":"422 Unprocessable Entity","message":"Request validation failed","data":[...]}
```

| HTTP | Условие | Тело / поведение |
|---|---|---|
| 400–599 от HTTP-исключения | HTTP ошибка | `message` равен текстовому `detail`, иначе `HTTP error` |
| 401 Unauthorized | отсутствует/не прошла аутентификация или авторизация | сообщение исключения, заголовок `WWW-Authenticate: Bearer` |
| 404 Not Found | сущность не найдена/недоступна | сообщение исключения |
| 409 Conflict | конфликт, включая конфликт версии | сообщение исключения |
| 410 Gone | курсор change log уже истёк | `data: {"resync_required":true,"restart_sequence":N}`; клиенту нужна полная синхронизация |
| 422 Unprocessable Entity | ошибка схемы или InvalidInput | для ошибок схемы `message: "Request validation failed"`, `data` — список ошибок Pydantic без `ctx`; для InvalidInput — текст исключения |
| 500 Internal Server Error | необработанная ошибка | `message: "Internal server error"`, детали не раскрываются |

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

## Связи проекта и устройства

| Метод и путь | Тело | Ответ |
|---|---|---|
| `POST /project_devices` | `project_id`, `device_id`, опционально `role` | `201 ProjectDeviceData` |
| `GET /project_devices/{project_device_id}` | — | связь |
| `GET /projects/{project_id}/devices` | — | связи устройств с проектом |
| `GET /devices/{device_id}/projects` | — | связи проекта с устройством |
| `PUT /project_devices/{project_device_id}` | `project_id`, `device_id`, опционально `role` | обновлённая связь |
| `DELETE /project_devices/{project_device_id}` | — | `200`, `data:null` |

`ProjectDeviceData`: `id`, `project_id`, `device_id`, `role`, `created_at`, `version`. Роль должна соответствовать доменному `ProjectDeviceRole`.

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
| `PUT /device-groups/{device_group_id}` | `name`, опционально `description` | группа |
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
| `POST /devices/{device_id}/metrics` | `metric_type`, `value`, `unit`, `collected_at`; опционально `source` | `201 MetricData`; устройство должно принадлежать пользователю |
| `GET /devices/{device_id}/metrics` | query `start`, `end` (интервал `[start, end)`), `limit` (100, 1–500), `offset` (0) | метрики устройства по убыванию времени сбора |

`MetricData`: `id`, `device_id`, `metric_type`, `value`, `unit`, `source`, `collected_at`. Значение — неотрицательное число с точностью до 6 десятичных знаков; время должно содержать часовой пояс. Диапазон может быть открыт с любой стороны, но если указаны обе границы, `start` должен предшествовать `end`. Метрики не записываются в ChangeLog как отдельные события.

## Настройки

| Метод и путь | Параметры/тело | Ответ |
|---|---|---|
| `GET /settings?scope=global` | — | глобальные настройки пользователя |
| `GET /settings?scope=client&client_device_id={uuid}` | — | настройки принадлежащего пользователю клиентского устройства |
| `GET /settings/{setting_id}` | — | настройка пользователя |
| `POST /settings` | `scope`, `key`, `value`; для `client` обязателен `client_device_id` | `201 SettingData` |
| `PUT /settings/{setting_id}` | `expected_version`, `value` | обновлённая `SettingData`, версия увеличивается на 1 |
| `DELETE /settings/{setting_id}?expected_version={version}` | — | `200`, `data:null` |

`SettingData`: `id`, `user_id`, `client_device_id`, `scope`, `key`, `value`, `version`, `created_at`, `updated_at`. `scope`: `global` или `client`. Ключ уникален в области видимости. Изменения записываются в ChangeLog; payload содержит область, ключ и ID устройства, но не значение настройки.

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

`ChangeLogData`: `id`, `user_id`, `entity_type`, `entity_id`, `operation`, `version`, `sequence`, `changed_by_client_id`, `changed_by_user_id`, `payload`, `created_at`. Операция: `insert`, `update`, `delete`. `EntityType` включает user/project/environment/project_device/device/device_group/device_group_member/connection/service/container/database и доменные типы repository, branch, commit, code_component, dependency, script, script_execution, relation, event, metric, settings, sync_state, other.

## Примечания к контракту

- UUID-параметры пути должны быть корректными UUID; иначе FastAPI вернёт 422.
- Ошибки предметной области `NotFound`, `InvalidInput`, `Conflict`, `Unauthorized` отображаются в 404/422/409/401 соответственно. Текст зависит от конкретного use case и не фиксирован этим документом.
- Запросы с неизвестными полями отклоняются. Для nullable полей отсутствие и `null` могут совпадать; отдельные PATCH-операции статуса перечислены выше.
- В API сейчас подключены только перечисленные маршруты. Наличие доменных сущностей в других модулях само по себе не означает наличие HTTP endpoint.
