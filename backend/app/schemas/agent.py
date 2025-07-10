"""
Agent schemas for AIRIES AI platform
Pydantic models for agent API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.agent import AgentType, AgentStatus


class AgentBase(BaseModel):
    """Base agent schema with common fields"""
    name: str = Field(..., min_length=2, max_length=200, description="Agent name")
    description: Optional[str] = Field(None, max_length=1000, description="Agent description")
    agent_type: AgentType = Field(default=AgentType.VOICE, description="Agent type (voice, chat, hybrid)")
    
    # Core configuration
    system_prompt: str = Field(..., min_length=10, description="System prompt for the agent")
    welcome_message: Optional[str] = Field(None, description="Welcome message for conversations")
    fallback_message: Optional[str] = Field(None, description="Fallback message for unclear inputs")
    max_conversation_length: Optional[int] = Field(50, ge=1, le=200, description="Maximum conversation turns")
    
    # LLM Configuration
    llm_provider: Optional[str] = Field("groq", description="LLM provider (groq, openai, deepinfra)")
    llm_model: Optional[str] = Field("mixtral-8x7b-32768", description="LLM model name")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum tokens per response")
    
    # Voice Configuration
    voice_provider: Optional[str] = Field(None, description="Voice provider (elevenlabs, azure, playht)")
    voice_id: Optional[str] = Field(None, description="Voice ID for TTS")
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice-specific settings")
    
    # STT Configuration
    stt_provider: Optional[str] = Field("deepgram", description="STT provider")
    stt_model: Optional[str] = Field("nova-2", description="STT model")
    stt_language: Optional[str] = Field("en", description="STT language code")
    
    # Telephony Configuration
    phone_number: Optional[str] = Field(None, description="Assigned phone number")
    sip_endpoint: Optional[str] = Field(None, description="SIP endpoint URL")
    telephony_provider: Optional[str] = Field(None, description="Telephony provider")
    
    # Knowledge Base Configuration
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base UUID")
    rag_enabled: Optional[bool] = Field(False, description="Enable RAG functionality")
    rag_similarity_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="RAG similarity threshold")
    rag_max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum RAG results")
    
    # Conversation Settings
    conversation_timeout: Optional[int] = Field(300, ge=30, le=3600, description="Conversation timeout in seconds")
    silence_timeout: Optional[int] = Field(10, ge=3, le=60, description="Silence timeout in seconds")
    interrupt_enabled: Optional[bool] = Field(True, description="Allow conversation interruptions")
    
    # Advanced Features
    tools_enabled: Optional[bool] = Field(False, description="Enable tool usage")
    available_tools: Optional[List[str]] = Field(None, description="List of available tools")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for events")
    webhook_events: Optional[List[str]] = Field(None, description="List of webhook events")
    
    # Scheduling and Availability
    is_available: Optional[bool] = Field(True, description="Agent availability status")
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="Weekly availability schedule")
    timezone: Optional[str] = Field("UTC", description="Agent timezone")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('llm_provider')
    def validate_llm_provider(cls, v):
        if v and v not in ['groq', 'openai', 'deepinfra']:
            raise ValueError('LLM provider must be one of: groq, openai, deepinfra')
        return v

    @validator('voice_provider')
    def validate_voice_provider(cls, v):
        if v and v not in ['elevenlabs', 'azure', 'playht']:
            raise ValueError('Voice provider must be one of: elevenlabs, azure, playht')
        return v

    @validator('stt_provider')
    def validate_stt_provider(cls, v):
        if v and v not in ['deepgram', 'whisper', 'azure']:
            raise ValueError('STT provider must be one of: deepgram, whisper, azure')
        return v

    @validator('telephony_provider')
    def validate_telephony_provider(cls, v):
        if v and v not in ['twilio', 'telnyx', 'custom']:
            raise ValueError('Telephony provider must be one of: twilio, telnyx, custom')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('Phone number must start with + and include country code')
        return v

    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Webhook URL must be a valid HTTP/HTTPS URL')
        return v


class AgentCreate(AgentBase):
    """Schema for creating a new agent"""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    agent_type: Optional[AgentType] = None
    
    # Core configuration
    system_prompt: Optional[str] = Field(None, min_length=10)
    welcome_message: Optional[str] = None
    fallback_message: Optional[str] = None
    max_conversation_length: Optional[int] = Field(None, ge=1, le=200)
    
    # LLM Configuration
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    
    # Voice Configuration
    voice_provider: Optional[str] = None
    voice_id: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = None
    
    # STT Configuration
    stt_provider: Optional[str] = None
    stt_model: Optional[str] = None
    stt_language: Optional[str] = None
    
    # Telephony Configuration
    phone_number: Optional[str] = None
    sip_endpoint: Optional[str] = None
    telephony_provider: Optional[str] = None
    
    # Knowledge Base Configuration
    knowledge_base_id: Optional[str] = None
    rag_enabled: Optional[bool] = None
    rag_similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    rag_max_results: Optional[int] = Field(None, ge=1, le=20)
    
    # Conversation Settings
    conversation_timeout: Optional[int] = Field(None, ge=30, le=3600)
    silence_timeout: Optional[int] = Field(None, ge=3, le=60)
    interrupt_enabled: Optional[bool] = None
    
    # Advanced Features
    tools_enabled: Optional[bool] = None
    available_tools: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    webhook_events: Optional[List[str]] = None
    
    # Scheduling and Availability
    is_available: Optional[bool] = None
    availability_schedule: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    @validator('llm_provider')
    def validate_llm_provider(cls, v):
        if v and v not in ['groq', 'openai', 'deepinfra']:
            raise ValueError('LLM provider must be one of: groq, openai, deepinfra')
        return v

    @validator('voice_provider')
    def validate_voice_provider(cls, v):
        if v and v not in ['elevenlabs', 'azure', 'playht']:
            raise ValueError('Voice provider must be one of: elevenlabs, azure, playht')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('Phone number must start with + and include country code')
        return v


class AgentResponse(BaseModel):
    """Schema for agent API responses"""
    id: str
    user_id: str
    account_id: str
    name: str
    description: Optional[str]
    agent_type: AgentType
    status: AgentStatus
    
    # Core configuration
    system_prompt: str
    welcome_message: Optional[str]
    fallback_message: Optional[str]
    max_conversation_length: int
    
    # LLM Configuration
    llm_provider: str
    llm_model: str
    temperature: float
    max_tokens: int
    
    # Voice Configuration
    voice_provider: Optional[str]
    voice_id: Optional[str]
    voice_settings: Optional[Dict[str, Any]]
    
    # STT Configuration
    stt_provider: str
    stt_model: str
    stt_language: str
    
    # Telephony Configuration
    phone_number: Optional[str]
    sip_endpoint: Optional[str]
    telephony_provider: Optional[str]
    
    # Knowledge Base Configuration
    knowledge_base_id: Optional[str]
    rag_enabled: bool
    rag_similarity_threshold: float
    rag_max_results: int
    
    # Conversation Settings
    conversation_timeout: int
    silence_timeout: int
    interrupt_enabled: bool
    
    # Advanced Features
    tools_enabled: bool
    available_tools: Optional[List[str]]
    webhook_url: Optional[str]
    webhook_events: Optional[List[str]]
    
    # Analytics and Monitoring
    total_conversations: int
    total_minutes: float
    total_tokens: int
    average_rating: Optional[float]
    response_time_avg: Optional[float]
    success_rate: float
    error_count: int
    
    # Scheduling and Availability
    is_available: bool
    availability_schedule: Optional[Dict[str, Any]]
    timezone: str
    
    # Computed properties
    is_voice_enabled: bool
    is_chat_enabled: bool
    has_phone_number: bool
    has_knowledge_base: bool
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    last_trained_at: Optional[datetime]
    last_used_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class AgentSummary(BaseModel):
    """Simplified agent schema for list views"""
    id: str
    name: str
    description: Optional[str]
    agent_type: AgentType
    status: AgentStatus
    is_available: bool
    total_conversations: int
    total_minutes: float
    average_rating: Optional[float]
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentTest(BaseModel):
    """Schema for testing agent responses"""
    input_text: str = Field(..., min_length=1, max_length=1000, description="Test input text")
    test_type: str = Field("text", description="Test type (text, voice, full)")
    include_context: bool = Field(False, description="Include conversation context")
    context_messages: Optional[List[Dict[str, str]]] = Field(None, description="Previous messages for context")

    @validator('test_type')
    def validate_test_type(cls, v):
        if v not in ['text', 'voice', 'full']:
            raise ValueError('Test type must be one of: text, voice, full')
        return v


class AgentTestResponse(BaseModel):
    """Schema for agent test responses"""
    success: bool
    input: str
    output: str
    response_time_ms: int
    tokens_used: int
    model_used: str
    provider_used: str
    timestamp: str
    error: Optional[str] = None


class AgentAnalytics(BaseModel):
    """Schema for agent analytics requests"""
    period: str = Field("7d", description="Analytics period (24h, 7d, 30d)")
    include_details: bool = Field(False, description="Include detailed metrics")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to include")

    @validator('period')
    def validate_period(cls, v):
        if v not in ['24h', '7d', '30d']:
            raise ValueError('Period must be one of: 24h, 7d, 30d')
        return v


class AgentAnalyticsResponse(BaseModel):
    """Schema for agent analytics responses"""
    agent_id: str
    agent_name: str
    period: str
    start_date: str
    end_date: str
    metrics: Dict[str, Any]
    usage_by_day: List[Dict[str, Any]]
    performance: Dict[str, Any]


class AgentValidation(BaseModel):
    """Schema for agent configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    agent_id: str
    agent_name: str


class AgentTemplate(BaseModel):
    """Schema for agent templates"""
    id: str
    name: str
    description: str
    agent_type: AgentType
    system_prompt: str
    welcome_message: str
    fallback_message: str
    llm_provider: str
    llm_model: str
    temperature: float
    conversation_timeout: int
    silence_timeout: int
    tools_enabled: Optional[bool] = False
    available_tools: Optional[List[str]] = None


class AgentClone(BaseModel):
    """Schema for cloning agents"""
    new_name: str = Field(..., min_length=2, max_length=200, description="Name for the cloned agent")
    copy_settings: bool = Field(True, description="Copy all configuration settings")
    copy_knowledge_base: bool = Field(False, description="Copy knowledge base reference")


class AgentDeployment(BaseModel):
    """Schema for agent deployment"""
    validate_config: bool = Field(True, description="Validate configuration before deployment")
    force_deploy: bool = Field(False, description="Force deployment even with warnings")


class AgentStats(BaseModel):
    """Schema for agent statistics"""
    total_agents: int
    active_agents: int
    inactive_agents: int
    agents_by_type: Dict[str, int]
    total_conversations: int
    total_minutes: float
    average_rating: Optional[float]