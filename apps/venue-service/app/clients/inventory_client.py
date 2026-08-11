import uuid
import structlog

from app.core.config import settings
from app.core.http import http_client

logger = structlog.get_logger(__name__)

class InventoryClient:
    @staticmethod
    async def get_available_seats(showtime_id: uuid.UUID, default_capacity: int) -> int:
        if not http_client.client:
            return default_capacity
        url = f"{settings.INVENTORY_SERVICE_URL}/api/v1/inventory/showtime/{showtime_id}/summary"
        try:
            response = await http_client.client.get(url, timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("available", default_capacity)
        except Exception as e:
            logger.warning(
                "Failed to fetch seat summary from inventory-service, falling back to full capacity",
                showtime_id=str(showtime_id),
                error=str(e)
            )
        return default_capacity

    @staticmethod
    async def get_seat_statuses(showtime_id: uuid.UUID) -> dict[str, str]:
        if not http_client.client:
            return {}
        url = f"{settings.INVENTORY_SERVICE_URL}/api/v1/inventory/showtime/{showtime_id}"
        try:
            response = await http_client.client.get(url, timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    inner_data = data.get("data", data)
                    if isinstance(inner_data, dict) and "seats" in inner_data:
                        return {item["seat_code"]: item["status"] for item in inner_data["seats"]}
                    if isinstance(inner_data, dict):
                        return inner_data
        except Exception as e:
            logger.warning(
                "Failed to fetch seat statuses from inventory-service, falling back to AVAILABLE",
                showtime_id=str(showtime_id),
                error=str(e)
            )
        return {}
