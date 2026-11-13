# Безопасность сетевого развёртывания

## Локальная разработка

Скопируйте `.env.example` в `.env`, задайте уникальный `POSTGRES_PASSWORD` и заполните все `AUTH_JWT_*` значения данными собственного Identity Service. Положите только предоставленный им публичный RSA PEM ключ в `.local/keys/jwt-public.pem`; `AUTH_JWT_PUBLIC_KEY_PATH` в `.env` указывает на этот файл. Compose подключает файл в контейнер Backend и change-log-pruner только для чтения. В частности, issuer и audience должны быть согласованы с Identity Service; не используйте фиктивные production значения. Не помещайте приватный signing key в репозиторий, build context, Docker image или логи. Каталог `.local/` исключён из Git. Запустите `docker compose up --build`. По умолчанию опубликованные порты PostgreSQL и Backend доступны только с хоста через loopback: `127.0.0.1:5432` и `127.0.0.1:8000`. API доступен по `http://127.0.0.1:8000`; health endpoints — `/api/v1/health` и `/api/v1/health/ready`.

Backend внутри Compose слушает `0.0.0.0:8000`, чтобы принимать соединения в своей Docker network. Это адрес интерфейсов контейнера, а не публичный host binding. Контейнеры в default Compose network могут обращаться к `http://backend:8000`; host port binding не ограничивает внутреннее взаимодействие.

## Production topology

Рекомендуется разместить reverse proxy/ingress и Backend в общей private Docker network. Публикуйте наружу только порты proxy (обычно 443, а при необходимости 80 для перенаправления на HTTPS); у Backend удалите `ports` в production override и подключите его к той же внутренней сети, что и proxy. Если proxy работает вне Docker, публикуйте Backend только на выделенном private interface через `BACKEND_BIND_ADDRESS` и дополнительно ограничьте доступ firewall/security group так, чтобы соединяться мог только proxy. Не задавайте `0.0.0.0` для host binding без документированной необходимости и сетевых ACL.

TLS завершается на reverse proxy. Внешние API запросы должны идти только по HTTPS; proxy должен перенаправлять HTTP на HTTPS и задавать HSTS согласно политике домена. Прямой доступ клиентов к HTTP Backend запрещается сетевой изоляцией/ACL, а не наличием TLS в приложении. Dockerfile запускает HTTP Uvicorn; это ожидаемо для TLS termination на proxy.

## Proxy headers и обязанности компонентов

Приложение не устанавливает `ProxyHeadersMiddleware`, не включает Uvicorn `--proxy-headers`, не задаёт `forwarded_allow_ips` и не читает `Forwarded`/`X-Forwarded-*` для формирования URL или client IP. Поэтому в текущем запуске эти заголовки не используются как источник доверенных данных. Не включайте обработку forwarded headers без настройки точного списка proxy IP/CIDR на ASGI server и проверки, что proxy удаляет входные от клиента значения и записывает собственные. Не доверяйте `*`/произвольным источникам.

Инфраструктура отвечает за сертификаты и TLS версии/шифры, HTTPS redirect, HSTS, сетевые ACL, доступность только ingress к Backend, изоляцию Docker networks, rate limiting и внешние лимиты. Приложение обеспечивает API-аутентификацию/авторизацию и security headers, но не удостоверяет production TLS и не ограничивает host network ACL. `TrustedHostMiddleware` не настроен; ограничивайте допустимые hostnames на ingress и добавляйте app-level trusted hosts только если определён стабильный набор доменов.

`ports` публикуют порт на host; отсутствие `ports` не препятствует доступу контейнеров, подключённых к общей Docker network. Используйте отдельные private networks для связности proxy/backend и избегайте подключения к ним недоверенных контейнеров.
