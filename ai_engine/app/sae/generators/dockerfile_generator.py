"""Deterministic Dockerfile & Docker Compose Generator for SAE v2."""

from __future__ import annotations

from typing import Any, Dict, Tuple


def generate_docker_scaffolds(
    system_name: str,
    backend_lld: Dict[str, Any],
    cloud_lld: Dict[str, Any],
) -> Tuple[str, str]:
    """Generate production multi-stage Dockerfile and full docker-compose.yml."""
    fw_config = backend_lld.get("framework_config", {})
    language = fw_config.get("language", "Python 3.11+")
    framework = fw_config.get("framework", "FastAPI")

    # ── Dockerfile Generation ───────────────────────────────────────────────
    if "python" in language.lower() or "fastapi" in framework.lower() or "django" in framework.lower() or "flask" in framework.lower():
        dockerfile = """# ── Stage 1: Build & Dependencies ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Minimal Distroless / Slim Runtime ──────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Non-root user for principle of least privilege
RUN groupadd -g 10001 appgroup && \\
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup . /app

ENV PATH=/home/appuser/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PORT=8000

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:8000/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""
    else:
        # Node.js / TypeScript default
        dockerfile = """# ── Stage 1: Build Dependencies ───────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── Stage 2: Production Runner ──────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && \\
    adduser --system --uid 1001 appuser
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \\
    CMD wget -qO- http://localhost:8000/live || exit 1
CMD ["node", "dist/main.js"]
"""

    # ── Docker Compose Generation ───────────────────────────────────────────
    docker_compose = f"""version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {system_name.lower().replace(' ', '_')}_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres_secret@postgres:5432/{system_name.lower().replace(' ', '_')}_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=dev_insecure_jwt_secret_change_in_production_32chars
      - CORS_ORIGINS=http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/live"]
      interval: 15s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:16-alpine
    container_name: {system_name.lower().replace(' ', '_')}_postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres_secret
      - POSTGRES_DB={system_name.lower().replace(' ', '_')}_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: {system_name.lower().replace(' ', '_')}_redis
    restart: unless-stopped
    command: ["redis-server", "--save", "60", "1", "--loglevel", "warning"]
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
"""

    return dockerfile, docker_compose
