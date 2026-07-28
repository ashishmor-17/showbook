import httpx

# Reusable client with built-in connection pool and timeout
http_client = httpx.AsyncClient(timeout=2.0)

async def get_http_client() -> httpx.AsyncClient:
    yield http_client
