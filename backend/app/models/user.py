"""
User model for AIRIES AI platform
Handles user accounts, authentication, and subscription tiers
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid
import enum
import secrets
import string

from ..core.database import Base


class UserTier(str, enum.Enum):
    """User subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


def generate_account_id() -> str:
    """Generate a unique account ID"""
    # Generate a 12-character alphanumeric account ID (e.g., ACC_A1B2C3D4E5F6)
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f"ACC_{random_part}"


class User(Base):
    """User model for authentication and account management"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Account identifier - unique account ID for logging and tracking
    account_id = Column(String(32), unique=True, index=True, nullable=False, default=generate_account_id)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Subscription and billing
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    credits = Column(Integer, default=1000, nullable=False)
    monthly_usage_limit = Column(Integer, nullable=True)
    
    # API access
    api_key = Column(String(64), unique=True, index=True, nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Verification
    verification_token = Column(String(255), nullable=True)
    verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    metadata = Column(Text, nullable=True)  # JSON string for flexible data
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tier={self.tier})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return self.tier in [UserTier.PRO, UserTier.ENTERPRISE]
    
    @property
    def concurrent_call_limit(self) -> int:
        """Get concurrent call limit based on tier"""
        limits = {
            UserTier.FREE: 2,
            UserTier.PRO: 10,
            UserTier.ENTERPRISE: 50
        }
        return limits.get(self.tier, 2)
    
    def can_make_call(self, current_calls: int) -> bool:
        """Check if user can make another call"""
        return current_calls < self.concurrent_call_limit
    
    def has_credits(self, required_credits: int) -> bool:
        """Check if user has enough credits"""
        return self.credits >= required_credits
    
    def deduct_credits(self, amount: int) -> bool:
        """Deduct credits from user account"""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)