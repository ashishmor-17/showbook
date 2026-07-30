import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class UserProfileResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_verified: bool

    class Config:
        from_attributes = True

class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
