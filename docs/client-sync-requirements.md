# Требования к синхронизации на клиенте

В документе описано, как клиент должен работать с API ChangeLog. Клиент хранит курсор ChangeLog вместе с локальным состоянием учётной записи и клиентского устройства.

## Обычная синхронизация изменений

1. Запросить `GET /change-logs?after_sequence=<cursor>&limit=100`.
2. Применить полученные записи по возрастанию `sequence`. Повторное применение записи должно быть безопасным: ориентируйтесь на идентификаторы и версии сущностей. Операцию `delete` обработайте как удаление сущности из локального хранилища.
3. Сохранить новый курсор только после надёжного применения всех записей ответа. Курсором становится номер последней применённой записи. Если ответ пустой, оставить текущий курсор.
4. Запрашивать следующие страницы, пока в ответе приходит 100 записей.

Если не удалось применить записи локально, не продвигайте курсор. После восстановления локального состояния повторите тот же запрос.

## Восстановление после HTTP 410

Если API вернул `410 Gone`, `data.resync_required: true` и `data.restart_sequence`:

1. Не менять старый курсор до завершения восстановления. Начать сборку нового локального состояния вместо применения изменений с устаревшего курсора.
2. Загрузить все коллекции из Sync Registry ниже через перечисленные owner-scoped API. Снимок — это протокол клиента, который объединяет ответы существующих endpoint-ов; отдельного серверного snapshot endpoint нет.
3. Собрать состояние из всех страниц/вложенных коллекций так, чтобы частично обновлённый кеш не был доступен приложению. Сохранить состояние атомарно или подготовить отдельно и переключить приложение только после успешного завершения всех необходимых запросов.
4. После успешного сохранения снимка записать `restart_sequence` как новый cursor.
5. Возобновить обычную синхронизацию запросом `GET /change-logs?after_sequence=<restart_sequence>`. Изменения, произошедшие после вычисления restart boundary, имеют большие номера последовательности и будут получены для применения.

Если не удался любой запрос снимка или его локальное сохранение, отбросить неполное состояние и оставить прежний cursor. Повторить восстановление; не сохранять `restart_sequence` заранее.

## Sync Registry

Registry — закрытый перечень текущих типов, которые одновременно имеют ChangeLog producer и owner-scoped способ прочитать актуальное состояние. Наличие значения в `EntityType` само по себе не включает сущность в Registry. Поля `id`, `entity_type`, `entity_id`, `operation`, `version`, `sequence` и actor/timestamp метаданные передаются общим `ChangeLogData`; в колонке payload перечислены дополнительные поля, записываемые producer-ом.

Для каждого snapshot после 410 клиент запрашивает полные актуальные данные следующими способами:

| EntityType | ChangeLog producer | Payload insert/update; delete | Полное текущее состояние | Восстановление после 410 и ограничения |
|---|---|---|---|---|
| `user` | создание пользователя | payload отсутствует | `GET /users/me` | Загрузить профиль владельца; событие содержит только envelope. |
| `project` | create/update/delete | `name`, `description`, `project_type`, `status`; delete без payload | `GET /projects` | Загрузить все проекты. |
| `environment` | create/update/delete | `project_id`, `name`, `environment_type`, `description`; delete без payload | `GET /projects/{project_id}/environments` | Сначала загрузить проекты, затем окружения каждого проекта. |
| `project_device` | link/update/delete | insert/update: `project_id`, `device_id`, `role`; delete без payload | `GET /projects/{project_id}/devices` | Сначала загрузить проекты, затем связи каждого проекта. |
| `device` | create/update/delete | `name`, `hostname`, `description`, `device_type`, `operating_system`, `os_version`, `architecture`, `tags`; delete без payload | `GET /devices` | Загрузить все устройства владельца. |
| `device_group` | create/update/delete | `name`, `description`; delete без payload | `GET /device-groups` | Загрузить группы, затем их участников. |
| `device_group_member` | add/remove member | `group_id`, `device_id` в insert и delete | `GET /device-groups/{group_id}/members` | Требуется обход всех загруженных групп. |
| `connection` | create/update/status/delete | `device_id`, `name`, `slug`, `host`, `port`, `username`, `authentication_type`, `connection_timeout`, `is_default`, `last_connected_at`, `last_status`; delete без payload | `GET /connections` | Загрузить подключения владельца. Секреты аутентификации в payload не включаются. |
| `service` | create/update/status/delete | `device_id`, `project_id`, `environment_id`, `name`, `service_type`, `description`, `system_identifier`, `status`; delete без payload | `GET /services` | Загрузить сервисы владельца. |
| `container` | create/update/delete | `container_runtime_id`, `device_id`, `project_id`, `environment_id`, `service_id`, `name`, `image`, `status`, `ports`, `volumes`, `networks`, `started_at`, `last_seen_at`; delete без payload | `GET /containers` | Загрузить контейнеры владельца. |
| `database` | create/update/delete | `device_id`, `project_id`, `environment_id`, `container_id`, `service_id`, `name`, `dbms_type`, `host`, `port`, `database_name`, `status`, `last_checked_at`; delete без payload | `GET /databases` | Загрузить базы данных владельца. |
| `repository` | create/update/delete | `project_id`, `name`, `default_branch`, `repository_type`; delete без payload | `GET /repositories` | Загрузить репозитории владельца. `remote_url` и `description` не входят в payload события. |
| `code_component` | create/update/delete | `repository_id`, `parent_id`, `name`, `path`, `component_type`, `language`, `symbol`, `start_line`, `end_line`, `analysis_version`, `analyzed_at`, `source_commit_hash`; delete без payload | `GET /repositories/{repository_id}/code-components` | Сначала загрузить репозитории, затем компоненты каждого репозитория. |
| `script` | create/update/delete | insert/update: `project_id`, `execution_type`, `risk_level`, `requires_confirmation`; delete без payload | `GET /scripts` | Загрузить Script полностью через API; ChangeLog не переносит `content`, `parameters` и остальные поля Script. |
| `settings` | create/update/delete | `scope`, `key`, `client_device_id`; значение настройки не включается, delete сохраняет эти метаданные | `GET /settings?scope=global`; `GET /settings?scope=client&client_device_id={client_device_id}` | Global и client scope известного устройства восстанавливаются. API не предоставляет список всех ClientDevice ID, поэтому нельзя перечислить client-scoped настройки всех устройств аккаунта только существующими маршрутами. |

Для JSON-полей `ports`, `volumes`, `networks`, `tags` и других перечисленных значений payload показывает текущую реализацию producer-а, а полное актуальное значение берётся из соответствующей GET-модели. При добавлении synced type необходимо обновить эту таблицу, определить producer payload, owner-scoped GET-путь и полный обход коллекции до использования типа клиентом.

### Типы вне Registry и открытая граница

`EntityType` также содержит типы, для которых сейчас не обнаружен ChangeLog producer: `branch`, `commit`, `dependency`, `script_target`, `script_execution`, `relation`, `event`, `log_metadata`, `metric`, `change_log`, `other`. Это enum values, а не обещание incremental sync. Для `event`, `log_metadata` и `metric` API-контракт отдельно говорит, что они не публикуются как ChangeLog-события.

`sync_state` имеет producer-ы CRUD/status, но не имеет list endpoint для полного owner-scoped восстановления. До отдельного архитектурного решения он не входит в поддерживаемый Registry для пользовательского snapshot; текущая серверная запись `SYNC_STATE` в общий ChangeLog не изменена. Поэтому полнота восстановления `SYNC_STATE` не гарантируется, если consumer считает каждое событие ChangeLog пользовательскими данными. Рекомендуемое отдельное решение — определить служебный sync state вне бизнес ChangeLog либо согласовать collection snapshot; ни одно из них в этой задаче не реализуется.

`settings` покрывает глобальные настройки и client scope только для известного `client_device_id`. Полное перечисление client-scoped настроек всех устройств остаётся нерешённым пробелом API, если это требуется продуктовой гарантией восстановления аккаунта.

## Гарантии backend и интеграционных проверок

- Страницы ChangeLog содержат только записи текущего пользователя, отсортированы по номеру последовательности и ограничены 100 записями на запрос.
- В ответе 410 номер `restart_sequence` не меньше последнего сохранённого номера последовательности пользователя на момент проверки устаревшего курсора.
- Интеграционный сценарий проверяет обнаружение устаревшего курсора, загрузку текущего снимка, изменение во время этой загрузки и продолжение опроса после `restart_sequence`.
