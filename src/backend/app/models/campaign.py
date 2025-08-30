"""
Campaign management models for Link Dive AI
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

class CampaignData(BaseModel):
    """Internal campaign data model used for database operations"""
    user_email: str
    client_name: str
    campaign_name: str
    client_domain: str
    campaign_url: Optional[str] = None
    launch_date: Optional[date] = None
    monitoring_status: str = "Live"
    auto_pause_date: Optional[date] = None
    serp_keywords: List[str] = Field(default_factory=list)
    verification_keywords: List[str] = Field(default_factory=list)
    blacklist_domains: List[str] = Field(default_factory=list)

class CampaignSearchRequest(BaseModel):
    """Campaign search/filter model"""
    user_email: str
    client_name: Optional[str] = None
    campaign_name: Optional[str] = None
    monitoring_status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

# We'll use SQLite initially with basic models
# These are the Pydantic models for API validation

class CampaignKeywordCreate(BaseModel):
    keyword_type: str = Field(..., pattern="^(serp|verification)$")
    keyword: str

class DomainBlacklistCreate(BaseModel):
    domain: str
    reason: Optional[str] = None

class CampaignCreate(BaseModel):
    """Campaign creation model"""
    client_name: str = Field(..., min_length=1, max_length=255)
    campaign_name: str = Field(..., min_length=1, max_length=255)
    client_domain: str = Field(..., min_length=1, max_length=255)
    campaign_url: Optional[str] = None
    launch_date: Optional[date] = None
    serp_keywords: List[str] = Field(default_factory=list)
    verification_keywords: List[str] = Field(default_factory=list)
    blacklist_domains: List[str] = Field(default_factory=list)

class CampaignUpdate(BaseModel):
    """Campaign update model"""
    client_name: Optional[str] = None
    campaign_name: Optional[str] = None
    client_domain: Optional[str] = None
    campaign_url: Optional[str] = None
    launch_date: Optional[date] = None
    monitoring_status: Optional[str] = None

class CampaignResponse(BaseModel):
    """Campaign response model"""
    id: int
    user_email: str
    client_name: str
    campaign_name: str
    client_domain: str
    campaign_url: Optional[str] = None
    launch_date: Optional[date] = None
    monitoring_status: str
    created_at: datetime
    updated_at: datetime
    auto_pause_date: Optional[date] = None

class BacklinkResultResponse(BaseModel):
    """Backlink result response model"""
    id: int
    url: str
    page_title: Optional[str] = None
    first_seen: Optional[date] = None
    coverage_status: str
    source_api: str
    domain_rating: Optional[int] = None
    confidence_score: Optional[str] = None

class CampaignResultsResponse(BaseModel):
    """Campaign with results response"""
    campaign: CampaignResponse
    results: List[BacklinkResultResponse]
    total_results: int
    verified_coverage: int
    potential_coverage: int

# In-memory storage for development (replace with database later)
class CampaignStorage:
    """Simple in-memory storage for campaigns during development"""
    
    def __init__(self):
        self.campaigns: List[dict] = []
        self.results: List[dict] = []
        self.next_id = 1
        self.next_result_id = 1
    
    def create_campaign(self, user_email: str, campaign_data: CampaignCreate) -> dict:
        """Create a new campaign"""
        campaign = {
            "id": self.next_id,
            "user_email": user_email,
            "client_name": campaign_data.client_name,
            "campaign_name": campaign_data.campaign_name,
            "client_domain": campaign_data.client_domain,
            "campaign_url": campaign_data.campaign_url,
            "launch_date": campaign_data.launch_date,
            "monitoring_status": "Live",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "auto_pause_date": None,
            "serp_keywords": campaign_data.serp_keywords,
            "verification_keywords": campaign_data.verification_keywords,
            "blacklist_domains": campaign_data.blacklist_domains
        }
        self.campaigns.append(campaign)
        self.next_id += 1
        return campaign
    
    def get_campaigns_by_user(self, user_email: str) -> List[dict]:
        """Get all campaigns for a user"""
        return [c for c in self.campaigns if c["user_email"] == user_email]
    
    def get_campaign_by_id(self, campaign_id: int, user_email: str) -> Optional[dict]:
        """Get campaign by ID for specific user"""
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id and campaign["user_email"] == user_email:
                return campaign
        return None
    
    def update_campaign(self, campaign_id: int, user_email: str, update_data: CampaignUpdate) -> Optional[dict]:
        """Update campaign"""
        campaign = self.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            if field in campaign:
                campaign[field] = value
        
        campaign["updated_at"] = datetime.utcnow()
        return campaign
    
    def delete_campaign(self, campaign_id: int, user_email: str) -> bool:
        """Delete campaign"""
        for i, campaign in enumerate(self.campaigns):
            if campaign["id"] == campaign_id and campaign["user_email"] == user_email:
                del self.campaigns[i]
                # Also delete associated results
                self.results = [r for r in self.results if r["campaign_id"] != campaign_id]
                return True
        return False

# Global storage instance
campaign_storage = CampaignStorage()
