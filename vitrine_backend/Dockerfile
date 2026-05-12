# Stage 1: Build frontend
FROM node:20-alpine AS frontend
WORKDIR /app
COPY vitrine_frontend/package.json vitrine_frontend/package-lock.json* ./
RUN npm install
COPY vitrine_frontend/ .
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY vitrine_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vitrine_backend/app/ ./app/
COPY --from=frontend /app/dist ./static_www/

RUN mkdir -p /app/data /app/logs /app/app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
