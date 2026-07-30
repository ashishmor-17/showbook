import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from showbook_common.database import transaction_scope

from app.models.profile import UserProfile
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password
from app.core.exceptions import UserNotFoundException, InvalidCredentialsException
from app.schemas.user import UserProfileResponse, UserProfileUpdateRequest
from app.schemas.auth import MessageResponse

class UserService:
    @classmethod
    async def get_profile(cls, db: AsyncSession, user_id: uuid.UUID) -> UserProfileResponse:
        user = await UserRepository.get_by_id_with_profile(db, user_id)
        if not user:
            raise UserNotFoundException()
        
        if not user.profile:
            async with transaction_scope(db):
                user.profile = UserProfile(user_id=user.id)
                db.add(user.profile)
        
        return UserProfileResponse(
            user_id=user.id,
            email=user.email,
            name=user.profile.name,
            phone=user.profile.phone,
            avatar=user.profile.avatar,
            preferences=user.profile.preferences,
            is_verified=user.is_verified
        )

    @classmethod
    async def update_profile(
        cls, db: AsyncSession, user_id: uuid.UUID, update_data: UserProfileUpdateRequest
    ) -> UserProfileResponse:
        async with transaction_scope(db):
            user = await UserRepository.get_by_id_with_profile(db, user_id)
            if not user:
                raise UserNotFoundException()
            
            if not user.profile:
                user.profile = UserProfile(user_id=user.id)
                db.add(user.profile)
            
            if update_data.name is not None:
                user.profile.name = update_data.name
            if update_data.phone is not None:
                user.profile.phone = update_data.phone
            if update_data.avatar is not None:
                user.profile.avatar = update_data.avatar
            if update_data.preferences is not None:
                # Merge or replace preferences
                user.profile.preferences = update_data.preferences
                
        return UserProfileResponse(
            user_id=user.id,
            email=user.email,
            name=user.profile.name,
            phone=user.profile.phone,
            avatar=user.profile.avatar,
            preferences=user.profile.preferences,
            is_verified=user.is_verified
        )

    @classmethod
    async def change_password(
        cls, db: AsyncSession, user_id: uuid.UUID, old_password: str, new_password: str
    ) -> MessageResponse:
        async with transaction_scope(db):
            user = await UserRepository.get_by_id(db, user_id)
            if not user:
                raise UserNotFoundException()
            
            if not verify_password(old_password, user.hashed_password):
                raise InvalidCredentialsException(message="Incorrect old password")
            
            user.hashed_password = hash_password(new_password)
            
        return MessageResponse(message="Password changed successfully")
