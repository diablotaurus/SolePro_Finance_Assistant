# Dockerfile for the SolePro Telegram bot.
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.13-slim

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system solepro \
    && useradd --system --gid solepro --home-dir /app solepro

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY --chown=solepro:solepro . .
RUN mkdir -p /app/data /app/logs /app/exports /app/backups \
    && chown -R solepro:solepro /app

USER solepro

CMD ["sh", "-c", "python scripts/init_db.py && exec python -m solepro.presentation.telegram.bot"]
