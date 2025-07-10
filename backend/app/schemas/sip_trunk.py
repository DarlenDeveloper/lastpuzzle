"""
Pydantic schemas for SIP trunk telephony system
Handles request/response validation for SIP trunk operations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.sip_trunk import SipTrunkStatus, SipTrunkProvider, CallDirection


# Base schemas
class SipTrunkBase(BaseModel):
    """Base SIP trunk schema"""
    name: str = Field(..., min_length=1, max_length=100, description="SIP trunk name")
    description: Optional[str] = Field(None, max_length=1000, description="SIP trunk description")
    provider: SipTrunkProvider = Field(..., description="SIP trunk provider")
    sip_domain: str = Field(..., min_length=1, max_length=255, description="SIP domain")
    sip_username: str = Field(..., min_length=1, max_length=100, description="SIP username")
    sip_port: int = Field(5060, ge=1, le=65535, description="SIP port")
    call_direction: CallDirection = Field(CallDirection.BIDIRECTIONAL, description="Call direction")
    max_concurrent_calls: int = Field(10, ge=1, le=1000, description="Maximum concurrent calls")


class SipTrunkCreate(SipTrunkBase):
    """Schema for creating a SIP trunk"""
    sip_password: str = Field(..., min_length=1, max_length=255, description="SIP password")
    auth_username: Optional[str] = Field(None, max_length=100, description="Authentication username")
    auth_password: Optional[str] = Field(None, max_length=255, description="Authentication password")
    sip_proxy: Optional[str] = Field(None, max_length=255, description="SIP proxy server")
    
    # Configuration
    inbound_routing: Optional[Dict[str, Any]] = Field(None, description="Inbound routing configuration")
    outbound_routing: Optional[Dict[str, Any]] = Field(None, description="Outbound routing configuration")
    codec_preferences: Optional[List[str]] = Field(None, description="Preferred codecs in order")
    dtmf_mode: str = Field("rfc2833", description="DTMF mode")
    
    # Billing
    cost_per_minute: float = Field(0.01, ge=0, description="Cost per minute")
    monthly_cost: float = Field(0.0, ge=0, description="Monthly cost")
    
    # Security
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses")
    encryption_enabled: bool = Field(True, description="Enable encryption")
    
    # Advanced
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom SIP headers")
    advanced_config: Optional[Dict[str, Any]] = Field(None, description="Advanced configuration")
    priority: int = Field(1, ge=1, le=100, description="Trunk priority")
    
    @validator('allowed_ips')
    def validate_ips(cls, v):
        if v is not None:
            import ipaddress
            for ip in v:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    raise ValueError(f"Invalid IP address: {ip}")
        return v


class SipTrunkUpdate(BaseModel):
    """Schema for updating a SIP trunk"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[SipTrunkStatus] = None
    sip_password: Optional[str] = Field(None, min_length=1, max_length=255)
    auth_username: Optional[str] = Field(None, max_length=100)
    auth_password: Optional[str] = Field(None, max_length=255)
    sip_proxy: Optional[str] = Field(None, max_length=255)
    sip_port: Optional[int] = Field(None, ge=1, le=65535)
    call_direction: Optional[CallDirection] = None
    max_concurrent_calls: Optional[int] = Field(None, ge=1, le=1000)
    
    # Configuration
    inbound_routing: Optional[Dict[str, Any]] = None
    outbound_routing: Optional[Dict[str, Any]] = None
    codec_preferences: Optional[List[str]] = None
    dtmf_mode: Optional[str] = None
    
    # Billing
    cost_per_minute: Optional[float] = Field(None, ge=0)
    monthly_cost: Optional[float] = Field(None, ge=0)
    
    # Security
    allowed_ips: Optional[List[str]] = None
    encryption_enabled: Optional[bool] = None
    
    # Advanced
    custom_headers: Optional[Dict[str, str]] = None
    advanced_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=100)


class SipTrunkResponse(SipTrunkBase):
    """Schema for SIP trunk response"""
    id: str = Field(..., description="SIP trunk ID")
    user_id: str = Field(..., description="User ID")
    status: SipTrunkStatus = Field(..., description="SIP trunk status")
    current_active_calls: int = Field(..., description="Current active calls")
    
    # Health monitoring
    last_health_check: Optional[datetime] = Field(None, description="Last health check")
    health_status: str = Field(..., description="Health status")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    packet_loss_percent: Optional[float] = Field(None, description="Packet loss percentage")
    
    # Billing
    cost_per_minute: float = Field(..., description="Cost per minute")
    monthly_cost: float = Field(..., description="Monthly cost")
    
    # Security
    encryption_enabled: bool = Field(..., description="Encryption enabled")
    
    # Metadata
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Computed properties
    utilization_percent: float = Field(..., description="Current utilization percentage")
    is_active: bool = Field(..., description="Is trunk active and healthy")
    can_handle_call: bool = Field(..., description="Can handle another call")
    
    class Config:
        from_attributes = True


class SipTrunkList(BaseModel):
    """Schema for SIP trunk list response"""
    trunks: List[SipTrunkResponse]
    total: int
    page: int
    size: int
    has_next: bool


class SipTrunkHealthCheck(BaseModel):
    """Schema for SIP trunk health check"""
    trunk_id: str
    status: str
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# Call Log schemas
class CallLogBase(BaseModel):
    """Base call log schema"""
    direction: CallDirection
    from_number: str = Field(..., min_length=1, max_length=20)
    to_number: str = Field(..., min_length=1, max_length=20)


class CallLogCreate(CallLogBase):
    """Schema for creating a call log"""
    call_id: str = Field(..., min_length=1, max_length=100)
    sip_trunk_id: str = Field(..., description="SIP trunk ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    started_at: datetime = Field(..., description="Call start time")
    status: str = Field(..., description="Call status")
    sip_call_id: Optional[str] = Field(None, max_length=255)
    remote_ip: Optional[str] = Field(None, max_length=45)
    metadata: Optional[Dict[str, Any]] = None


class CallLogUpdate(BaseModel):
    """Schema for updating a call log"""
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: Optional[str] = None
    hangup_cause: Optional[str] = Field(None, max_length=50)
    quality_score: Optional[float] = Field(None, ge=1, le=5)
    codec_used: Optional[str] = Field(None, max_length=20)
    duration_seconds: Optional[int] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    credits_used: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class CallLogResponse(CallLogBase):
    """Schema for call log response"""
    id: str
    user_id: str
    sip_trunk_id: str
    conversation_id: Optional[str]
    call_id: str
    
    # Timing
    started_at: datetime
    answered_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    
    # Status and quality
    status: str
    hangup_cause: Optional[str]
    quality_score: Optional[float]
    
    # Technical details
    codec_used: Optional[str]
    sip_call_id: Optional[str]
    remote_ip: Optional[str]
    
    # Billing
    cost: float
    credits_used: int
    
    # Metadata
    created_at: datetime
    
    # Computed properties
    is_completed: bool
    was_answered: bool
    
    class Config:
        from_attributes = True


class CallLogList(BaseModel):
    """Schema for call log list response"""
    calls: List[CallLogResponse]
    total: int
    page: int
    size: int
    has_next: bool


class CallLogStats(BaseModel):
    """Schema for call log statistics"""
    total_calls: int
    answered_calls: int
    failed_calls: int
    total_duration_minutes: float
    total_cost: float
    average_duration_seconds: float
    answer_rate_percent: float
    quality_score_average: Optional[float]


# SIP trunk statistics
class SipTrunkStats(BaseModel):
    """Schema for SIP trunk statistics"""
    trunk_id: str
    trunk_name: str
    total_calls: int
    active_calls: int
    utilization_percent: float
    health_status: str
    last_24h_calls: int
    last_24h_duration_minutes: float
    last_24h_cost: float
    uptime_percent: float


class SipTrunkDashboard(BaseModel):
    """Schema for SIP trunk dashboard"""
    total_trunks: int
    active_trunks: int
    total_active_calls: int
    total_capacity: int
    overall_utilization_percent: float
    trunk_stats: List[SipTrunkStats]
    recent_calls: List[CallLogResponse]
    call_stats: CallLogStats


# WebRTC and real-time communication schemas
class WebRTCOffer(BaseModel):
    """Schema for WebRTC offer"""
    sdp: str = Field(..., description="SDP offer")
    type: str = Field("offer", description="SDP type")
    trunk_id: str = Field(..., description="SIP trunk ID")


class WebRTCAnswer(BaseModel):
    """Schema for WebRTC answer"""
    sdp: str = Field(..., description="SDP answer")
    type: str = Field("answer", description="SDP type")


class ICECandidate(BaseModel):
    """Schema for ICE candidate"""
    candidate: str = Field(..., description="ICE candidate")
    sdp_mid: Optional[str] = Field(None, description="SDP media ID")
    sdp_m_line_index: Optional[int] = Field(None, description="SDP media line index")


# Telephony provider specific schemas
class TwilioConfig(BaseModel):
    """Twilio-specific configuration"""
    account_sid: str
    auth_token: str
    phone_number: str
    webhook_url: Optional[str] = None


class TelnyxConfig(BaseModel):
    """Telnyx-specific configuration"""
    api_key: str
    connection_id: str
    phone_number: str
    webhook_url: Optional[str] = None


class ProviderConfig(BaseModel):
    """Provider-specific configuration union"""
    provider: SipTrunkProvider
    config: Dict[str, Any]  # Will contain provider-specific config