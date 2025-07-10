"""
Pydantic schemas for AIRIES AI platform
Request/response models for API endpoints
"""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserRegister,
    TokenResponse, PasswordReset, PasswordResetConfirm
)
from .agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentSummary,
    AgentTest, AgentTestResponse, AgentAnalytics, AgentAnalyticsResponse,
    AgentValidation, AgentTemplate, AgentClone, AgentDeployment, AgentStats
)
from .conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationList, MessageCreate, MessageResponse, ConversationStats
)
from .usage import (
    UsageLogResponse, CreditTransactionResponse, UsageSummaryResponse,
    BillingPlanResponse, SubscriptionResponse, UsageStats
)
from .knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    DocumentUpload, DocumentResponse, QueryRequest, QueryResponse,
    WebScrapeJobCreate, WebScrapeJobResponse
)
from .sip_trunk import (
    SipTrunkCreate, SipTrunkUpdate, SipTrunkResponse, SipTrunkList,
    CallLogCreate, CallLogUpdate, CallLogResponse, CallLogList,
    SipTrunkStats, SipTrunkDashboard, SipTrunkHealthCheck,
    WebRTCOffer, WebRTCAnswer, ICECandidate
)

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "UserRegister",
    "TokenResponse", "PasswordReset", "PasswordResetConfirm",
    
    # Agent schemas
    "AgentCreate", "AgentUpdate", "AgentResponse", "AgentSummary",
    "AgentTest", "AgentTestResponse", "AgentAnalytics", "AgentAnalyticsResponse",
    "AgentValidation", "AgentTemplate", "AgentClone", "AgentDeployment", "AgentStats",
    
    # Conversation schemas
    "ConversationCreate", "ConversationUpdate", "ConversationResponse",
    "ConversationList", "MessageCreate", "MessageResponse", "ConversationStats",
    
    # Usage schemas
    "UsageLogResponse", "CreditTransactionResponse", "UsageSummaryResponse",
    "BillingPlanResponse", "SubscriptionResponse", "UsageStats",
    
    # Knowledge schemas
    "KnowledgeBaseCreate", "KnowledgeBaseUpdate", "KnowledgeBaseResponse",
    "DocumentUpload", "DocumentResponse", "QueryRequest", "QueryResponse",
    "WebScrapeJobCreate", "WebScrapeJobResponse",
    
    # SIP Trunk schemas
    "SipTrunkCreate", "SipTrunkUpdate", "SipTrunkResponse", "SipTrunkList",
    "CallLogCreate", "CallLogUpdate", "CallLogResponse", "CallLogList",
    "SipTrunkStats", "SipTrunkDashboard", "SipTrunkHealthCheck",
    "WebRTCOffer", "WebRTCAnswer", "ICECandidate"
]