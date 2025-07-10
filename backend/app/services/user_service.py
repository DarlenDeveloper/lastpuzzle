"""
User service for AIRIES AI platform
Handles user-related business logic and database operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from ..models.user import User, UserTier, UserStatus
from ..schemas.user import UserCreate, UserRegister, UserUpdate
from ..core.security import get_password_hash, generate_reset_token, generate_api_key
from ..core.logging import get_logger
from .account_service import ensure_user_has_account_id, log_account_activity, AccountContextManager


class UserService:
    """Service class for user operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def create_user(self, user_data: UserRegister) -> User:
        """Create a new user account"""
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user instance
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company=user_data.company,
            tier=UserTier.FREE,
            status=UserStatus.PENDING,
            credits=1000,  # Free tier credits
            is_active=True,
            is_verified=False
        )
        
        # Generate verification token
        user.verification_token = generate_reset_token()
        user.verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Add to database
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Ensure user has account ID
        account_id = await ensure_user_has_account_id(self.db, user)
        
        # Log user creation with account context
        async with AccountContextManager(account_id, str(user.id)):
            self.logger.log_user_action(
                action="create_user",
                resource="user",
                resource_id=str(user.id),
                extra_data={
                    'email': user.email,
                    'tier': user.tier,
                    'company': user.company
                }
            )
            
            await log_account_activity(
                self.db,
                account_id,
                'user_created',
                'user',
                str(user.id),
                {
                    'email': user.email,
                    'tier': user.tier,
                    'initial_credits': user.credits
                }
            )
        
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_uuid = uuid.UUID(user_id)
            result = await self.db.execute(
                select(User).where(User.id == user_uuid)
            )
            return result.scalar_one_or_none()
        except (ValueError, TypeError):
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        result = await self.db.execute(
            select(User).where(User.api_key == api_key)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """Update user password"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    hashed_password=hashed_password,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(last_login=datetime.utcnow())
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def increment_failed_attempts(self, user_id: str) -> bool:
        """Increment failed login attempts"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.increment_failed_attempts()
        await self.db.commit()
        return True
    
    async def reset_failed_attempts(self, user_id: str) -> bool:
        """Reset failed login attempts"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.reset_failed_attempts()
        await self.db.commit()
        return True
    
    async def generate_password_reset_token(self, user_id: str) -> bool:
        """Generate password reset token"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.password_reset_token = generate_reset_token()
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        await self.db.commit()
        return True
    
    async def verify_password_reset_token(self, token: str) -> Optional[User]:
        """Verify password reset token"""
        result = await self.db.execute(
            select(User).where(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()
    
    async def clear_password_reset_token(self, user_id: str) -> bool:
        """Clear password reset token"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    password_reset_token=None,
                    password_reset_expires=None
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def generate_verification_token(self, user_id: str) -> bool:
        """Generate email verification token"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.verification_token = generate_reset_token()
        user.verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        await self.db.commit()
        return True
    
    async def verify_email_token(self, token: str) -> Optional[User]:
        """Verify email verification token"""
        result = await self.db.execute(
            select(User).where(
                User.verification_token == token,
                User.verification_expires > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()
    
    async def mark_email_verified(self, user_id: str) -> bool:
        """Mark user email as verified"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    is_verified=True,
                    status=UserStatus.ACTIVE,
                    verification_token=None,
                    verification_expires=None
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def generate_api_key(self, user_id: str) -> Optional[str]:
        """Generate new API key for user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        api_key = f"ak_{generate_api_key()}"
        user.api_key = api_key
        user.api_key_created_at = datetime.utcnow()
        
        await self.db.commit()
        return api_key
    
    async def revoke_api_key(self, user_id: str) -> bool:
        """Revoke user's API key"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    api_key=None,
                    api_key_created_at=None
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def update_credits(self, user_id: str, credits: int) -> bool:
        """Update user credits"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(credits=credits)
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def deduct_credits(self, user_id: str, amount: int) -> bool:
        """Deduct credits from user account"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        if user.credits >= amount:
            user.credits -= amount
            await self.db.commit()
            return True
        
        return False
    
    async def upgrade_tier(self, user_id: str, tier: UserTier) -> bool:
        """Upgrade user tier"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(tier=tier)
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def suspend_user(self, user_id: str, reason: Optional[str] = None) -> bool:
        """Suspend user account"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    status=UserStatus.SUSPENDED,
                    is_active=False
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def reactivate_user(self, user_id: str) -> bool:
        """Reactivate suspended user account"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    status=UserStatus.ACTIVE,
                    is_active=True
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user account"""
        try:
            user_uuid = uuid.UUID(user_id)
            await self.db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    status=UserStatus.DELETED,
                    is_active=False,
                    deleted_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            return True
        except Exception:
            return False
    
    async def get_user_stats(self, user_id: str) -> Optional[dict]:
        """Get user statistics"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # TODO: Implement actual stats calculation
        # This would involve querying related tables for agents, conversations, etc.
        
        return {
            "total_agents": 0,
            "total_conversations": 0,
            "total_minutes": 0.0,
            "total_tokens": 0,
            "credits_used_this_month": 0,
            "credits_remaining": user.credits,
            "current_concurrent_calls": 0
        }