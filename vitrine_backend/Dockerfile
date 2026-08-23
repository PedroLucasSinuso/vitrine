# syntax=docker/dockerfile:1
#
# Build multi-stage do backend Vitrine (FastAPI + uv).
#
# Bibliotecas de sistema necessárias em runtime:
#   - libpq5            -> psycopg2 (conexão ao Postgres do ERP)
#   - libpango/libcairo/libgdk-pixbuf -> WeasyPrint (relatórios em PDF)

FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ── Stage de build: compila dependências (precisa de headers/compilador) ──
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY . .
RUN uv sync --frozen --no-dev

# ── Stage final: só o necessário para rodar ──
FROM base AS runtime
WORKDIR /app
RUN useradd --create-home --uid 1000 vitrine
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /app/data && chown -R vitrine:vitrine /app
USER vitrine
EXPOSE 8000

# init_db() aplica as migrações do Alembic automaticamente no startup
# (ver app/infrastructure/db/bootstrap.py) — nenhum passo manual necessário.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
