FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

COPY packages/python/pyproject.toml packages/python/
COPY apps/catalog-service/pyproject.toml apps/catalog-service/
COPY apps/scraper/pyproject.toml apps/scraper/
COPY apps/user-service/pyproject.toml apps/user-service/
COPY apps/venue-service/pyproject.toml apps/venue-service/

RUN uv sync --frozen --package scraper-service

COPY . .

RUN uv sync --frozen --package scraper-service

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/apps/scraper

CMD ["python", "run.py"]
