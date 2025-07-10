"""
SIP Trunk model for AIRIES AI telephony platform
Handles SIP trunk configuration, routing, and management
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Enum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class SipTrunkStatus(str, enum.Enum):
    """SIP trunk status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class SipTrunkProvider(str, enum.Enum):
    """SIP trunk providers"""
    TWILIO = "twilio"
    TELNYX = "telnyx"
    BANDWIDTH = "bandwidth"
    VONAGE = "vonage"
    CUSTOM = "custom"


class CallDirection(str, enum.Enum):
    """Call direction types"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SipTrunk(Base):
    """SIP Trunk configuration model"""
    
    __tablename__ = "sip_trunks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Basic configuration
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(Enum(SipTrunkProvider), nullable=False)
    status = Column(Enum(SipTrunkStatus), default=SipTrunkStatus.INACTIVE, nullable=False)
    
    # SIP configuration
    sip_domain = Column(String(255), nullable=False)
    sip_username = Column(String(100), nullable=False)
    sip_password = Column(String(255), nullable=False)
    sip_proxy = Column(String(255), nullable=True)
    sip_port = Column(Integer, default=5060, nullable=False)
    
    # Authentication
    auth_username = Column(String(100), nullable=True)
    auth_password = Column(String(255), nullable=True)
    
    # Routing configuration
    inbound_routing = Column(JSONB, nullable=True)  # JSON configuration for inbound routing
    outbound_routing = Column(JSONB, nullable=True)  # JSON configuration for outbound routing
    call_direction = Column(Enum(CallDirection), default=CallDirection.BIDIRECTIONAL, nullable=False)
    
    # Capacity and limits
    max_concurrent_calls = Column(Integer, default=10, nullable=False)
    current_active_calls = Column(Integer, default=0, nullable=False)
    
    # Quality settings
    codec_preferences = Column(JSONB, nullable=True)  # Preferred codecs in order
    dtmf_mode = Column(String(20), default="rfc2833", nullable=False)
    
    # Monitoring and health
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), default="unknown", nullable=False)
    latency_ms = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    
    # Billing and usage
    cost_per_minute = Column(Float, default=0.01, nullable=False)
    monthly_cost = Column(Float, default=0.0, nullable=False)
    
    # Security settings
    allowed_ips = Column(JSONB, nullable=True)  # Array of allowed IP addresses
    encryption_enabled = Column(Boolean, default=True, nullable=False)
    
    # Failover configuration
    failover_trunk_id = Column(UUID(as_uuid=True), ForeignKey("sip_trunks.id"), nullable=True)
    priority = Column(Integer, default=1, nullable=False)  # Lower number = higher priority
    
    # Advanced settings
    custom_headers = Column(JSONB, nullable=True)  # Custom SIP headers
    advanced_config = Column(JSONB, nullable=True)  # Provider-specific configuration
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sip_trunks")
    failover_trunk = relationship("SipTrunk", remote_side=[id])
    call_logs = relationship("CallLog", back_populates="sip_trunk")
    
    def __repr__(self) -> str:
        return f"<SipTrunk(id={self.id}, name={self.name}, provider={self.provider}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if trunk is active and healthy"""
        return self.status == SipTrunkStatus.ACTIVE and self.health_status == "healthy"
    
    @property
    def can_handle_call(self) -> bool:
        """Check if trunk can handle another call"""
        return (self.is_active and 
                self.current_active_calls < self.max_concurrent_calls)
    
    @property
    def utilization_percent(self) -> float:
        """Get current utilization percentage"""
        if self.max_concurrent_calls == 0:
            return 0.0
        return (self.current_active_calls / self.max_concurrent_calls) * 100
    
    def increment_active_calls(self) -> bool:
        """Increment active call count if possible"""
        if self.can_handle_call:
            self.current_active_calls += 1
            return True
        return False
    
    def decrement_active_calls(self) -> None:
        """Decrement active call count"""
        if self.current_active_calls > 0:
            self.current_active_calls -= 1
    
    def update_health_status(self, status: str, latency: float | None = None, packet_loss: float | None = None) -> None:
        """Update trunk health status"""
        self.health_status = status
        self.last_health_check = datetime.utcnow()
        if latency is not None:
            self.latency_ms = latency
        if packet_loss is not None:
            self.packet_loss_percent = packet_loss


class CallLog(Base):
    """Call log model for tracking SIP trunk usage"""
    
    __tablename__ = "call_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Associations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    sip_trunk_id = Column(UUID(as_uuid=True), ForeignKey("sip_trunks.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Call details
    call_id = Column(String(100), unique=True, nullable=False, index=True)
    direction = Column(Enum(CallDirection), nullable=False)
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    
    # Call timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Call status and quality
    status = Column(String(20), nullable=False)  # ringing, answered, busy, failed, etc.
    hangup_cause = Column(String(50), nullable=True)
    quality_score = Column(Float, nullable=True)  # 1-5 quality rating
    
    # Technical details
    codec_used = Column(String(20), nullable=True)
    sip_call_id = Column(String(255), nullable=True)
    remote_ip = Column(String(45), nullable=True)
    
    # Billing
    cost = Column(Float, default=0.0, nullable=False)
    credits_used = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)  # Additional call metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="call_logs")
    sip_trunk = relationship("SipTrunk", back_populates="call_logs")
    conversation = relationship("Conversation", back_populates="call_logs")
    
    def __repr__(self) -> str:
        return f"<CallLog(id={self.id}, call_id={self.call_id}, direction={self.direction}, status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if call is completed"""
        return self.ended_at is not None
    
    @property
    def was_answered(self) -> bool:
        """Check if call was answered"""
        return self.answered_at is not None
    
    def calculate_duration(self) -> int:
        """Calculate call duration in seconds"""
        if self.answered_at and self.ended_at:
            duration = (self.ended_at - self.answered_at).total_seconds()
            self.duration_seconds = int(duration)
            return self.duration_seconds
        return 0
    
    def calculate_cost(self, rate_per_minute: float) -> float:
        """Calculate call cost based on duration and rate"""
        if self.duration_seconds:
            minutes = self.duration_seconds / 60.0
            self.cost = minutes * rate_per_minute
            return self.cost
        return 0.0