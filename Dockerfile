FROM node:24-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY agents ./agents
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY main.py .
COPY README.md .
COPY .env.example .
COPY frontend/package.json ./frontend/package.json
COPY frontend/package-lock.json ./frontend/package-lock.json
COPY --from=frontend-build /app/backend/static ./backend/static

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
