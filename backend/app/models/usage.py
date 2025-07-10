"""
Usage tracking models for AIRIES AI platform
Handles billing, credits, and usage analytics
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class UsageType(str, enum.Enum):
    """Usage type enumeration"""
    VOICE_MINUTES = "voice_minutes"
    TOKENS = "tokens"
    STORAGE_MB = "storage_mb"
    API_CALLS = "api_calls"
    PHONE_CALLS = "phone_calls"
    TRANSCRIPTION_MINUTES = "transcription_minutes"
    TTS_CHARACTERS = "tts_characters"
    KNOWLEDGE_QUERIES = "knowledge_queries"


class BillingPeriod(str, enum.Enum):
    """Billing period enumeration"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    PAY_AS_YOU_GO = "pay_as_you_go"


class UsageLog(Base):
    """Usage tracking for billing and analytics"""
    
    __tablename__ = "usage_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Usage details
    usage_type = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # minutes, tokens, mb, calls, etc.
    
    # Cost calculation
    rate_per_unit = Column(Float, nullable=False)
    cost_credits = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=True)
    
    # Billing information
    billing_period = Column(String(20), nullable=True)
    invoice_id = Column(String(100), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User")
    agent = relationship("Agent")
    conversation = relationship("Conversation")
    
    def __repr__(self) -> str:
        return f"<UsageLog(id={self.id}, type={self.usage_type}, amount={self.amount})>"


class CreditTransaction(Base):
    """Credit transactions for user accounts"""
    
    __tablename__ = "credit_transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # purchase, usage, refund, bonus
    amount = Column(Integer, nullable=False)  # Positive for credits added, negative for usage
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Payment information
    payment_method = Column(String(50), nullable=True)  # stripe, paystack, manual
    payment_id = Column(String(100), nullable=True)
    payment_status = Column(String(20), nullable=True)
    
    # Description and metadata
    description = Column(Text, nullable=True)
    reference_id = Column(String(100), nullable=True)  # Reference to usage log or payment
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CreditTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class UsageSummary(Base):
    """Daily/monthly usage summaries for analytics"""
    
    __tablename__ = "usage_summaries"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Time period
    period_type = Column(String(10), nullable=False)  # daily, monthly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Usage metrics
    total_conversations = Column(Integer, default=0, nullable=False)
    total_voice_minutes = Column(Float, default=0.0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    total_api_calls = Column(Integer, default=0, nullable=False)
    total_storage_mb = Column(Float, default=0.0, nullable=False)
    
    # Cost metrics
    total_cost_credits = Column(Integer, default=0, nullable=False)
    total_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Performance metrics
    average_response_time = Column(Float, nullable=True)
    success_rate = Column(Float, default=1.0, nullable=False)
    user_satisfaction = Column(Float, nullable=True)  # Average rating
    
    # Detailed breakdown
    usage_breakdown = Column(JSONB, nullable=True)  # Detailed usage by type
    cost_breakdown = Column(JSONB, nullable=True)   # Detailed cost by type
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    agent = relationship("Agent")
    
    def __repr__(self) -> str:
        return f"<UsageSummary(id={self.id}, period={self.period_type}, user_id={self.user_id})>"


class BillingPlan(Base):
    """Billing plans and pricing tiers"""
    
    __tablename__ = "billing_plans"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Plan details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    tier = Column(String(20), nullable=False)  # free, pro, enterprise
    
    # Pricing
    monthly_price_usd = Column(Float, default=0.0, nullable=False)
    yearly_price_usd = Column(Float, default=0.0, nullable=False)
    included_credits = Column(Integer, default=0, nullable=False)
    
    # Limits
    max_agents = Column(Integer, nullable=True)
    max_concurrent_calls = Column(Integer, default=1, nullable=False)
    max_storage_mb = Column(Integer, nullable=True)
    max_monthly_minutes = Column(Integer, nullable=True)
    
    # Features
    features = Column(JSONB, nullable=True)  # List of included features
    rate_limits = Column(JSONB, nullable=True)  # API rate limits
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<BillingPlan(id={self.id}, name={self.name}, tier={self.tier})>"


class UserSubscription(Base):
    """User subscription to billing plans"""
    
    __tablename__ = "user_subscriptions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    billing_plan_id = Column(UUID(as_uuid=True), ForeignKey("billing_plans.id"), nullable=False)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Subscription details
    status = Column(String(20), default="active", nullable=False)  # active, cancelled, expired
    billing_period = Column(String(20), default="monthly", nullable=False)
    
    # Payment information
    stripe_subscription_id = Column(String(100), nullable=True)
    paystack_subscription_id = Column(String(100), nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    period_usage = Column(JSONB, nullable=True)  # Current period usage
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    billing_plan = relationship("BillingPlan")
    
    def __repr__(self) -> str:
        return f"<UserSubscription(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active" and datetime.utcnow() < self.current_period_end
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in current period"""
        if self.current_period_end:
            delta = self.current_period_end - datetime.utcnow()
            return max(0, delta.days)
        return 0