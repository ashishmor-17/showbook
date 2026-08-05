import httpx

class HttpClient:
    client: httpx.AsyncClient | None = None

    def start(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

http_client = HttpClient()
