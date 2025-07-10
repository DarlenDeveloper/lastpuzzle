"""
Database models for AIRIES AI platform
"""

from .user import User, UserTier, UserStatus
from .agent import Agent, AgentStatus, AgentType
from .conversation import Conversation, ConversationMessage, ConversationStatus, ConversationType
from .usage import (
    UsageLog, CreditTransaction, UsageSummary, BillingPlan, UserSubscription,
    UsageType, BillingPeriod
)
from .knowledge import (
    KnowledgeBase, Document, DocumentChunk, WebScrapeJob, QueryLog,
    DocumentStatus, DocumentType
)
from .sip_trunk import (
    SipTrunk, CallLog, SipTrunkStatus, SipTrunkProvider, CallDirection
)

# Add relationships after all models are imported
def setup_relationships():
    """Setup SQLAlchemy relationships between models"""
    
    # User relationships
    User.agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    User.conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    User.knowledge_bases = relationship("KnowledgeBase", back_populates="user", cascade="all, delete-orphan")
    User.usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    User.credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    User.usage_summaries = relationship("UsageSummary", back_populates="user", cascade="all, delete-orphan")
    User.subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    User.documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    User.web_scrape_jobs = relationship("WebScrapeJob", back_populates="user", cascade="all, delete-orphan")
    User.query_logs = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    User.sip_trunks = relationship("SipTrunk", back_populates="user", cascade="all, delete-orphan")
    User.call_logs = relationship("CallLog", back_populates="user", cascade="all, delete-orphan")

# Import relationship function
from sqlalchemy.orm import relationship

__all__ = [
    "User", "UserTier", "UserStatus",
    "Agent", "AgentStatus", "AgentType",
    "Conversation", "ConversationMessage", "ConversationStatus", "ConversationType",
    "UsageLog", "CreditTransaction", "UsageSummary", "BillingPlan", "UserSubscription",
    "UsageType", "BillingPeriod",
    "KnowledgeBase", "Document", "DocumentChunk", "WebScrapeJob", "QueryLog",
    "DocumentStatus", "DocumentType",
    "SipTrunk", "CallLog", "SipTrunkStatus", "SipTrunkProvider", "CallDirection",
    "setup_relationships"
]