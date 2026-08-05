FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

COPY packages/python/pyproject.toml packages/python/
COPY apps/catalog-service/pyproject.toml apps/catalog-service/
COPY apps/scraper/pyproject.toml apps/scraper/
COPY apps/user-service/pyproject.toml apps/user-service/
COPY apps/venue-service/pyproject.toml apps/venue-service/
COPY apps/payment-service/pyproject.toml apps/payment-service/
COPY apps/notification-service/pyproject.toml apps/notification-service/

RUN uv sync --frozen --package notification-service

COPY . .

RUN uv sync --frozen --package notification-service

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8008

WORKDIR /app/apps/notification-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
