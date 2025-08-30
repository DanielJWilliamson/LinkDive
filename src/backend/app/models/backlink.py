"""
Backlink data models for Link Dive AI.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, HttpUrl, Field


class LinkType(str, Enum):
    """Types of backlinks."""
    DOFOLLOW = "dofollow"
    NOFOLLOW = "nofollow"
    SPONSORED = "sponsored"
    UGC = "ugc"


class BacklinkStatus(str, Enum):
    """Status of backlinks."""
    ACTIVE = "active"
    LOST = "lost"
    REDIRECT = "redirect"
    BROKEN = "broken"


class Backlink(BaseModel):
    """Individual backlink model."""
    id: Optional[str] = None
    url_from: HttpUrl
    url_to: HttpUrl
    anchor_text: str
    first_seen: datetime
    last_seen: datetime
    link_type: LinkType
    status: BacklinkStatus = BacklinkStatus.ACTIVE
    
    # SEO Metrics
    domain_rating: Optional[int] = Field(None, ge=0, le=100)
    url_rating: Optional[int] = Field(None, ge=0, le=100)
    ahrefs_rank: Optional[int] = None
    traffic_value: Optional[int] = None
    
    # Link Properties
    is_content: bool = True
    is_redirect: bool = False
    is_canonical: bool = False
    is_image: bool = False
    is_frame: bool = False
    
    # Context Information
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    page_title: Optional[str] = None
    page_lang: Optional[str] = None
    
    # Data Source
    data_source: str  # "ahrefs", "dataforseo", "custom"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReferringDomain(BaseModel):
    """Referring domain summary model."""
    domain: str
    domain_rating: Optional[int] = Field(None, ge=0, le=100)
    backlinks_count: int = 0
    first_seen: datetime
    last_seen: datetime
    
    # Domain Metrics
    organic_traffic: Optional[int] = None
    organic_keywords: Optional[int] = None
    ahrefs_rank: Optional[int] = None
    
    # Link Distribution
    dofollow_links: int = 0
    nofollow_links: int = 0
    
    # Quality Indicators
    spam_score: Optional[float] = Field(None, ge=0, le=100)
    trust_score: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BacklinkProfile(BaseModel):
    """Complete backlink profile for a target."""
    target_url: HttpUrl
    target_domain: str
    
    # Summary Statistics
    total_backlinks: int = 0
    total_referring_domains: int = 0
    dofollow_backlinks: int = 0
    nofollow_backlinks: int = 0
    
    # Quality Metrics
    average_domain_rating: Optional[float] = None
    highest_domain_rating: Optional[int] = None
    total_traffic_value: Optional[int] = None
    
    # Growth Metrics
    new_backlinks_30d: int = 0
    lost_backlinks_30d: int = 0
    net_growth_30d: int = 0
    
    # Analysis Metadata
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)
    analysis_depth: str = "basic"  # basic, comprehensive, full
    data_sources: List[str] = []
    
    # Collections
    backlinks: List[Backlink] = []
    referring_domains: List[ReferringDomain] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BacklinkTrend(BaseModel):
    """Backlink trend data over time."""
    date: datetime
    total_backlinks: int
    referring_domains: int
    new_backlinks: int
    lost_backlinks: int
    net_growth: int
    average_dr: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnchorTextDistribution(BaseModel):
    """Anchor text analysis."""
    anchor_text: str
    count: int
    percentage: float
    link_type_distribution: Dict[LinkType, int]
    average_dr: Optional[float] = None
    first_seen: datetime
    last_seen: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
