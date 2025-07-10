"""
Agent model for AIRIES AI platform
Handles AI agent configurations, settings, and metadata
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    ARCHIVED = "archived"


class AgentType(str, enum.Enum):
    """Agent type enumeration"""
    VOICE = "voice"
    CHAT = "chat"
    HYBRID = "hybrid"


class Agent(Base):
    """Agent model for AI conversational agents"""
    
    __tablename__ = "agents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Basic information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(String(20), default=AgentType.VOICE, nullable=False)
    status = Column(String(20), default=AgentStatus.INACTIVE, nullable=False)
    
    # Agent configuration
    system_prompt = Column(Text, nullable=False)
    welcome_message = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    max_conversation_length = Column(Integer, default=50, nullable=False)
    
    # LLM Configuration
    llm_provider = Column(String(50), default="groq", nullable=False)  # groq, openai, deepinfra
    llm_model = Column(String(100), default="mixtral-8x7b-32768", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=1000, nullable=False)
    
    # Voice Configuration
    voice_provider = Column(String(50), nullable=True)  # elevenlabs, azure, playht
    voice_id = Column(String(100), nullable=True)
    voice_settings = Column(JSONB, nullable=True)  # Voice-specific settings
    
    # STT Configuration
    stt_provider = Column(String(50), default="deepgram", nullable=False)
    stt_model = Column(String(100), default="nova-2", nullable=False)
    stt_language = Column(String(10), default="en", nullable=False)
    
    # Telephony Configuration
    phone_number = Column(String(20), nullable=True)
    sip_endpoint = Column(String(200), nullable=True)
    telephony_provider = Column(String(50), nullable=True)  # twilio, telnyx
    
    # Knowledge Base
    knowledge_base_id = Column(UUID(as_uuid=True), nullable=True)
    rag_enabled = Column(Boolean, default=False, nullable=False)
    rag_similarity_threshold = Column(Float, default=0.7, nullable=False)
    rag_max_results = Column(Integer, default=5, nullable=False)
    
    # Conversation Settings
    conversation_timeout = Column(Integer, default=300, nullable=False)  # seconds
    silence_timeout = Column(Integer, default=10, nullable=False)  # seconds
    interrupt_enabled = Column(Boolean, default=True, nullable=False)
    
    # Advanced Features
    tools_enabled = Column(Boolean, default=False, nullable=False)
    available_tools = Column(JSONB, nullable=True)  # List of enabled tools
    webhook_url = Column(String(500), nullable=True)
    webhook_events = Column(JSONB, nullable=True)  # List of events to send
    
    # Analytics and Monitoring
    total_conversations = Column(Integer, default=0, nullable=False)
    total_minutes = Column(Float, default=0.0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    average_rating = Column(Float, nullable=True)
    
    # Performance Metrics
    response_time_avg = Column(Float, nullable=True)  # Average response time in ms
    success_rate = Column(Float, default=1.0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Scheduling and Availability
    is_available = Column(Boolean, default=True, nullable=False)
    availability_schedule = Column(JSONB, nullable=True)  # Weekly schedule
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_trained_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    metadata = Column(JSONB, nullable=True)  # Flexible metadata storage
    
    # Relationships
    user = relationship("User", back_populates="agents")
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type})>"
    
    @property
    def is_voice_enabled(self) -> bool:
        """Check if agent supports voice interactions"""
        return self.agent_type in [AgentType.VOICE, AgentType.HYBRID]
    
    @property
    def is_chat_enabled(self) -> bool:
        """Check if agent supports chat interactions"""
        return self.agent_type in [AgentType.CHAT, AgentType.HYBRID]
    
    @property
    def has_phone_number(self) -> bool:
        """Check if agent has a phone number assigned"""
        return self.phone_number is not None
    
    @property
    def has_knowledge_base(self) -> bool:
        """Check if agent has a knowledge base configured"""
        return self.knowledge_base_id is not None and self.rag_enabled
    
    def can_handle_call(self) -> bool:
        """Check if agent can handle incoming calls"""
        return (
            self.status == AgentStatus.ACTIVE and
            self.is_available and
            self.is_voice_enabled and
            self.has_phone_number
        )
    
    def update_usage_stats(self, minutes: float, tokens: int) -> None:
        """Update agent usage statistics"""
        self.total_conversations += 1
        self.total_minutes += minutes
        self.total_tokens += tokens
        self.last_used_at = datetime.utcnow()
    
    def update_performance_metrics(self, response_time: float, success: bool) -> None:
        """Update agent performance metrics"""
        # Update average response time
        if self.response_time_avg is None:
            self.response_time_avg = response_time
        else:
            # Simple moving average
            self.response_time_avg = (self.response_time_avg + response_time) / 2
        
        # Update success rate
        total_calls = self.total_conversations
        if total_calls > 0:
            current_successes = self.success_rate * (total_calls - 1)
            if success:
                current_successes += 1
            self.success_rate = current_successes / total_calls
        
        # Update error count
        if not success:
            self.error_count += 1
    
    def is_available_now(self) -> bool:
        """Check if agent is available at current time"""
        if not self.is_available:
            return False
        
        if not self.availability_schedule:
            return True
        
        # TODO: Implement schedule checking logic
        # This would check current time against availability_schedule
        return True
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration as dictionary"""
        return {
            "provider": self.llm_provider,
            "model": self.llm_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def get_voice_config(self) -> dict:
        """Get voice configuration as dictionary"""
        config = {
            "provider": self.voice_provider,
            "voice_id": self.voice_id
        }
        
        if self.voice_settings:
            config.update(self.voice_settings)
        
        return config
    
    def get_stt_config(self) -> dict:
        """Get STT configuration as dictionary"""
        return {
            "provider": self.stt_provider,
            "model": self.stt_model,
            "language": self.stt_language
        }