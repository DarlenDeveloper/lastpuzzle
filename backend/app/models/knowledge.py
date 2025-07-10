"""
Knowledge base models for AIRIES AI platform
Handles document storage, embeddings, and RAG functionality
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    WEB_PAGE = "web_page"
    API_DATA = "api_data"


class KnowledgeBase(Base):
    """Knowledge base container for documents and embeddings"""
    
    __tablename__ = "knowledge_bases"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Basic information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    embedding_model = Column(String(100), default="text-embedding-ada-002", nullable=False)
    chunk_size = Column(Integer, default=1000, nullable=False)
    chunk_overlap = Column(Integer, default=200, nullable=False)
    
    # Statistics
    total_documents = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    total_size_mb = Column(Float, default=0.0, nullable=False)
    
    # ChromaDB collection
    collection_name = Column(String(100), nullable=False, unique=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, documents={self.total_documents})>"


class Document(Base):
    """Individual documents within a knowledge base"""
    
    __tablename__ = "documents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Document information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    document_type = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # File details
    file_size_bytes = Column(Integer, nullable=False)
    file_url = Column(String(1000), nullable=True)  # Storage URL
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    
    # Processing status
    status = Column(String(20), default=DocumentStatus.PENDING, nullable=False)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Content extraction
    extracted_text = Column(Text, nullable=True)
    text_length = Column(Integer, default=0, nullable=False)
    language = Column(String(10), nullable=True)
    
    # Chunking information
    total_chunks = Column(Integer, default=0, nullable=False)
    chunk_size = Column(Integer, nullable=True)
    chunk_overlap = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    user = relationship("User")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
    
    @property
    def is_processed(self) -> bool:
        """Check if document is fully processed"""
        return self.status == DocumentStatus.COMPLETED
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size_bytes / (1024 * 1024)


class DocumentChunk(Base):
    """Text chunks from documents for embedding and retrieval"""
    
    __tablename__ = "document_chunks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_length = Column(Integer, nullable=False)
    
    # Position in document
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    
    # Embedding information
    embedding_id = Column(String(100), nullable=True)  # ChromaDB ID
    embedding_model = Column(String(100), nullable=True)
    embedding_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    knowledge_base = relationship("KnowledgeBase")
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class WebScrapeJob(Base):
    """Web scraping jobs for knowledge base updates"""
    
    __tablename__ = "web_scrape_jobs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Job configuration
    url = Column(String(2000), nullable=False)
    max_pages = Column(Integer, default=10, nullable=False)
    max_depth = Column(Integer, default=2, nullable=False)
    follow_links = Column(Boolean, default=True, nullable=False)
    
    # Scheduling
    schedule_type = Column(String(20), nullable=True)  # once, daily, weekly, monthly
    schedule_config = Column(JSONB, nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), default="pending", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    pages_scraped = Column(Integer, default=0, nullable=False)
    pages_failed = Column(Integer, default=0, nullable=False)
    total_content_length = Column(Integer, default=0, nullable=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase")
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<WebScrapeJob(id={self.id}, url={self.url}, status={self.status})>"


class QueryLog(Base):
    """Log of knowledge base queries for analytics"""
    
    __tablename__ = "query_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Account identifier for logging and tracking
    account_id = Column(String(32), nullable=False, index=True)
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_embedding_id = Column(String(100), nullable=True)
    
    # Results
    results_count = Column(Integer, default=0, nullable=False)
    top_similarity_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Usage
    tokens_used = Column(Integer, default=0, nullable=False)
    cost_credits = Column(Integer, default=0, nullable=False)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase")
    user = relationship("User")
    conversation = relationship("Conversation")
    
    def __repr__(self) -> str:
        return f"<QueryLog(id={self.id}, knowledge_base_id={self.knowledge_base_id}, results={self.results_count})>"