import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    recipient: str
    type: str
    channel: str
    subject: Optional[str] = None
    body: str
    notification_payload: dict
    status: str
    retry_count: int
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NotificationFeedResponse(BaseModel):
    items: List[NotificationResponse]
    next_cursor: Optional[str] = None
