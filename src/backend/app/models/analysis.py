"""
Analysis and insights models for Link Dive AI.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class AnalysisType(str, Enum):
    """Types of analysis available."""
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    RISK_ASSESSMENT = "risk_assessment"
    GROWTH_TRACKING = "growth_tracking"
    ANCHOR_ANALYSIS = "anchor_analysis"
    CONTENT_ANALYSIS = "content_analysis"


class Severity(str, Enum):
    """Severity levels for issues and recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QualityScore(BaseModel):
    """Comprehensive quality score breakdown."""
    overall_score: float = Field(..., ge=0, le=100)
    
    # Component Scores
    domain_authority_score: float = Field(..., ge=0, le=100)
    relevance_score: float = Field(..., ge=0, le=100)
    diversity_score: float = Field(..., ge=0, le=100)
    velocity_score: float = Field(..., ge=0, le=100)
    natural_score: float = Field(..., ge=0, le=100)
    spam_risk_score: float = Field(..., ge=0, le=100)
    
    # Grade
    grade: str  # A+, A, B+, B, C+, C, D, F
    
    # Explanation
    strengths: List[str] = []
    weaknesses: List[str] = []
    score_explanation: str = ""
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_level: float = Field(..., ge=0, le=100)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompetitorInsight(BaseModel):
    """Competitor analysis insights."""
    competitor_domain: str
    competitor_url: Optional[HttpUrl] = None
    
    # Metrics Comparison
    domain_rating: Optional[int] = Field(None, ge=0, le=100)
    total_backlinks: int = 0
    referring_domains: int = 0
    organic_traffic: Optional[int] = None
    
    # Comparative Analysis
    common_referring_domains: int = 0
    unique_referring_domains: int = 0
    backlink_gap: int = 0
    advantage_score: float = Field(..., ge=0, le=100)
    
    # Opportunities
    gap_opportunities: List[str] = []
    competitive_advantages: List[str] = []
    
    # Analysis
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LinkOpportunity(BaseModel):
    """Link building opportunity."""
    target_domain: str
    target_url: Optional[HttpUrl] = None
    
    # Metrics
    domain_rating: Optional[int] = Field(None, ge=0, le=100)
    organic_traffic: Optional[int] = None
    relevance_score: float = Field(..., ge=0, le=100)
    difficulty_score: float = Field(..., ge=0, le=100)
    potential_value: float = Field(..., ge=0, le=100)
    
    # Opportunity Details
    opportunity_type: str  # guest_post, resource_page, broken_link, etc.
    contact_method: Optional[str] = None
    contact_info: Optional[str] = None
    
    # Strategy
    suggested_approach: str
    pitch_template: Optional[str] = None
    estimated_success_rate: Optional[float] = Field(None, ge=0, le=100)
    
    # Context
    reason: str
    supporting_evidence: List[str] = []
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = "medium"  # low, medium, high
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RiskAlert(BaseModel):
    """SEO risk alert."""
    risk_type: str
    severity: Severity
    title: str
    description: str
    
    # Impact Assessment
    potential_impact: str
    affected_urls: List[str] = []
    affected_domains: List[str] = []
    
    # Recommendations
    recommendation: str
    action_items: List[str] = []
    priority: int = Field(..., ge=1, le=10)
    
    # Timeline
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_fix_time: Optional[str] = None
    
    # Evidence
    supporting_data: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GrowthMetric(BaseModel):
    """Growth tracking metric."""
    metric_name: str
    current_value: Union[int, float]
    previous_value: Union[int, float]
    change_absolute: Union[int, float]
    change_percentage: float
    period_days: int = 30
    
    # Trend Analysis
    trend_direction: str  # up, down, stable
    trend_strength: str  # weak, moderate, strong
    is_significant: bool = False
    
    # Context
    benchmark_value: Optional[Union[int, float]] = None
    industry_average: Optional[Union[int, float]] = None
    
    # Metadata
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Recommendation(BaseModel):
    """SEO recommendation."""
    title: str
    description: str
    category: str  # link_building, content, technical, etc.
    priority: str = "medium"  # low, medium, high
    
    # Implementation
    action_steps: List[str] = []
    estimated_effort: str  # low, medium, high
    estimated_timeline: str  # days, weeks, months
    
    # Expected Impact
    expected_benefit: str
    success_metrics: List[str] = []
    
    # Supporting Data
    reasoning: str
    supporting_evidence: List[str] = []
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0, le=100)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ComprehensiveAnalysis(BaseModel):
    """Comprehensive SEO analysis result."""
    target_url: HttpUrl
    target_domain: str
    
    # Core Analysis
    quality_score: QualityScore
    competitor_insights: List[CompetitorInsight] = []
    opportunities: List[LinkOpportunity] = []
    risk_alerts: List[RiskAlert] = []
    growth_metrics: List[GrowthMetric] = []
    recommendations: List[Recommendation] = []
    
    # Analysis Metadata
    analysis_types: List[AnalysisType] = []
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None
    data_sources: List[str] = []
    
    # Summary
    executive_summary: str = ""
    key_findings: List[str] = []
    next_steps: List[str] = []
    
    # Configuration
    analysis_depth: str = "comprehensive"  # basic, comprehensive, deep
    confidence_level: float = Field(..., ge=0, le=100)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
