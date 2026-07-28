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

RUN uv sync --frozen --package catalog-service

COPY . .

RUN uv sync --frozen --package catalog-service

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

WORKDIR /app/apps/catalog-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
