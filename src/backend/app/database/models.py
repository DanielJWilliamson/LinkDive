"""
Database models for Link Dive AI campaigns and analysis results
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, DECIMAL, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Campaign(Base):
    """Campaign model for storing PR campaign information"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    client_name = Column(String(255), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    client_domain = Column(String(255), nullable=False)
    campaign_url = Column(Text, nullable=True)
    launch_date = Column(Date, nullable=True)
    monitoring_status = Column(String(20), default="Live")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    auto_pause_date = Column(Date, nullable=True)
    last_backlink_fetch_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    keywords = relationship("CampaignKeyword", back_populates="campaign", cascade="all, delete-orphan")
    blacklist_domains = relationship("DomainBlacklist", back_populates="campaign", cascade="all, delete-orphan")
    backlink_results = relationship("BacklinkResult", back_populates="campaign", cascade="all, delete-orphan")
    serp_rankings = relationship("SerpRanking", back_populates="campaign", cascade="all, delete-orphan")

class CampaignKeyword(Base):
    """Keywords associated with campaigns (SERP monitoring or verification)"""
    __tablename__ = "campaign_keywords"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    keyword_type = Column(String(20), nullable=False)  # 'serp' or 'verification'
    keyword = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="keywords")

class DomainBlacklist(Base):
    """Domains to exclude from campaign results"""
    __tablename__ = "domain_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="blacklist_domains")

class BacklinkResult(Base):
    """Backlink analysis results for campaigns"""
    __tablename__ = "backlink_results"
    __table_args__ = (
        UniqueConstraint('campaign_id', 'url', 'source_api', name='uq_backlink_unique'),
        Index('ix_backlink_campaign_status', 'campaign_id', 'coverage_status'),
        Index('ix_backlink_campaign_destination', 'campaign_id', 'link_destination'),
    )

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    page_title = Column(Text, nullable=True)
    first_seen = Column(Date, nullable=True)
    last_seen = Column(Date, nullable=True)
    coverage_status = Column(String(20), nullable=False)  # 'verified', 'potential'
    source_api = Column(String(20), nullable=False)  # 'ahrefs', 'dataforseo', 'serp'
    domain_rating = Column(Integer, nullable=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    content_analysis = Column(JSON, nullable=True)  # Store keyword matches and analysis
    link_destination = Column(String(30), nullable=True)  # blog_page | homepage | other
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="backlink_results")

class SerpRanking(Base):
    """SERP ranking tracking for campaigns"""
    __tablename__ = "serp_rankings"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    position = Column(Integer, nullable=True)
    page_title = Column(Text, nullable=True)
    check_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="serp_rankings")


class ContentAnalysis(Base):
    """Content analysis results tied to a backlink result (detailed coverage verification)."""
    __tablename__ = "content_analysis"

    id = Column(Integer, primary_key=True, index=True)
    backlink_result_id = Column(Integer, ForeignKey("backlink_results.id", ondelete="CASCADE"), nullable=False)
    keyword_hits = Column(JSON, nullable=True)
    score = Column(DECIMAL(3, 2), nullable=True)
    hash = Column(String(64), nullable=True, index=True)
    raw_excerpt = Column(Text, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

class BackgroundTask(Base):
    """Background task tracking"""
    __tablename__ = "background_tasks"

    id = Column(String(255), primary_key=True)  # Task ID
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True)
    user_email = Column(String(255), nullable=False, index=True)
    parameters = Column(JSON, nullable=True)
    progress = Column(DECIMAL(5, 2), default=0.0)  # 0.00 to 100.00
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)


class RateLimitState(Base):
    """Persistent token bucket state for external API rate limiting."""
    __tablename__ = "rate_limit_state"

    name = Column(String(50), primary_key=True, index=True)
    tokens = Column(DECIMAL(10, 2), nullable=False)
    capacity = Column(Integer, nullable=False)
    rate_per_minute = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
