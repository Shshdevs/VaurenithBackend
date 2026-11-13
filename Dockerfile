FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ENV PYTHONPATH=/app/src

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app

COPY requirements.txt .

RUN pip install --no-cache-dir --no-compile -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY scripts ./scripts
COPY src ./src

RUN chown -R app:app /app

USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=5)" || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
