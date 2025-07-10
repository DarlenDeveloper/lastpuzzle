"""
Conversation model for AIRIES AI platform
Handles conversation sessions, call records, and interaction history
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ConversationType(str, enum.Enum):
    """Conversation type enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    TEST = "test"


class CallDirection(str, enum.Enum):
    """Call direction enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Conversation(Base):
    """Conversation model for tracking agent interactions"""
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Session information
    session_id = Column(String(100), nullable=False, index=True)
    conversation_type = Column(String(20), default=ConversationType.INBOUND, nullable=False)
    status = Column(String(20), default=ConversationStatus.ACTIVE, nullable=False)
    
    # Contact information
    caller_phone = Column(String(20), nullable=True)
    caller_name = Column(String(200), nullable=True)
    caller_location = Column(String(200), nullable=True)
    
    # Call details
    call_direction = Column(String(20), nullable=True)
    call_sid = Column(String(100), nullable=True, index=True)  # Twilio/Telnyx call ID
    sip_call_id = Column(String(200), nullable=True)  # SIP call ID
    
    # Timing information
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    
    # Usage tracking
    total_tokens = Column(Integer, default=0, nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_cost_credits = Column(Integer, default=0, nullable=False)
    
    # Audio and transcription
    recording_url = Column(String(500), nullable=True)
    recording_duration = Column(Float, nullable=True)
    transcript = Column(Text, nullable=True)
    
    # Quality metrics
    audio_quality_score = Column(Float, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    response_time_avg = Column(Float, nullable=True)  # Average response time in ms
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_feedback = Column(Text, nullable=True)
    
    # Technical details
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    country_code = Column(String(2), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Conversation flow
    message_count = Column(Integer, default=0, nullable=False)
    interruption_count = Column(Integer, default=0, nullable=False)
    silence_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional metadata
    metadata = Column(JSONB, nullable=True)  # Flexible metadata storage
    conversation_data = Column(JSONB, nullable=True)  # Full conversation history
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, session_id={self.session_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if conversation is currently active"""
        return self.status == ConversationStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        """Check if conversation is completed"""
        return self.status in [ConversationStatus.COMPLETED, ConversationStatus.FAILED, ConversationStatus.TIMEOUT]
    
    @property
    def duration_minutes(self) -> float:
        """Get conversation duration in minutes"""
        return self.duration_seconds / 60.0 if self.duration_seconds else 0.0
    
    @property
    def cost_per_minute(self) -> float:
        """Calculate cost per minute"""
        if self.duration_minutes > 0:
            return self.total_cost_credits / self.duration_minutes
        return 0.0
    
    def start_conversation(self) -> None:
        """Mark conversation as started"""
        self.answered_at = datetime.utcnow()
        self.status = ConversationStatus.ACTIVE
    
    def end_conversation(self, status: ConversationStatus = ConversationStatus.COMPLETED) -> None:
        """End the conversation and calculate duration"""
        self.ended_at = datetime.utcnow()
        self.status = status
        
        if self.answered_at:
            duration = self.ended_at - self.answered_at
            self.duration_seconds = int(duration.total_seconds())
    
    def add_usage(self, input_tokens: int, output_tokens: int, cost_credits: int) -> None:
        """Add token usage and cost to conversation"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        self.total_cost_credits += cost_credits
    
    def add_message(self) -> None:
        """Increment message count"""
        self.message_count += 1
    
    def add_interruption(self) -> None:
        """Increment interruption count"""
        self.interruption_count += 1
    
    def add_silence(self) -> None:
        """Increment silence count"""
        self.silence_count += 1
    
    def set_error(self, error_message: str, error_code: str = None) -> None:
        """Set error information"""
        self.error_message = error_message
        self.error_code = error_code
        self.status = ConversationStatus.FAILED
    
    def set_rating(self, rating: int, feedback: str = None) -> None:
        """Set user rating and feedback"""
        if 1 <= rating <= 5:
            self.user_rating = rating
        if feedback:
            self.user_feedback = feedback
    
    def get_conversation_summary(self) -> dict:
        """Get conversation summary as dictionary"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "status": self.status,
            "duration_minutes": self.duration_minutes,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "total_cost_credits": self.total_cost_credits,
            "user_rating": self.user_rating,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }


class ConversationMessage(Base):
    """Individual messages within a conversation"""
    
    __tablename__ = "conversation_messages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message details
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # Processing details
    tokens_used = Column(Integer, default=0, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"