"""
Campaign management service for Link Dive AI
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from ..models.campaign import (
    CampaignCreate, 
    CampaignUpdate, 
    CampaignResponse,
    CampaignResultsResponse,
    BacklinkResultResponse,
    CampaignData
)
from ..database.database import SessionLocal
from ..database.repository import CampaignRepository, campaign_to_dict
from .link_analysis_service import LinkAnalysisService
from .campaign_analysis_service import campaign_analysis_service

class CampaignService:
    """Service for managing PR campaigns"""
    
    def __init__(self):
        self.link_analyzer = LinkAnalysisService()
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    async def create_campaign(self, user_email: str, campaign_data: CampaignCreate) -> CampaignResponse:
        """Create a new campaign"""
        # Validate domain format
        if not self._is_valid_domain(campaign_data.client_domain):
            raise ValueError("Invalid domain format")
        
        # Set auto-pause date if launch date is provided
        auto_pause_date = None
        if campaign_data.launch_date:
            auto_pause_date = campaign_data.launch_date + timedelta(days=365)
        
        # Convert to internal data format
        internal_data = CampaignData(
            user_email=user_email,
            client_name=campaign_data.client_name,
            campaign_name=campaign_data.campaign_name,
            client_domain=campaign_data.client_domain,
            campaign_url=campaign_data.campaign_url,
            launch_date=campaign_data.launch_date or date.today(),
            monitoring_status="Live",
            auto_pause_date=auto_pause_date,
            serp_keywords=campaign_data.serp_keywords,
            verification_keywords=campaign_data.verification_keywords,
            blacklist_domains=campaign_data.blacklist_domains or []
        )
        
        # Save to database
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            db_campaign = repo.create_campaign(internal_data)
            campaign_dict = campaign_to_dict(db_campaign)
            return CampaignResponse(**campaign_dict)
        finally:
            db.close()
    
    async def get_campaigns(self, user_email: str) -> List[CampaignResponse]:
        """Get all campaigns for a user"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            campaigns = repo.get_campaigns_by_user(user_email)
            return [CampaignResponse(**campaign_to_dict(campaign)) for campaign in campaigns]
        finally:
            db.close()
    
    async def get_campaign(self, campaign_id: int, user_email: str) -> Optional[CampaignResponse]:
        """Get campaign by ID"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            campaign = repo.get_campaign_by_id(campaign_id, user_email)
            if campaign:
                campaign_dict = campaign_to_dict(campaign)
                return CampaignResponse(**campaign_dict)
            return None
        finally:
            db.close()
    
    async def update_campaign(self, campaign_id: int, user_email: str, update_data: CampaignUpdate) -> Optional[CampaignResponse]:
        """Update campaign"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            campaign = repo.get_campaign_by_id(campaign_id, user_email)
            if not campaign:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(campaign, field):
                    setattr(campaign, field, value)
            
            # Update timestamp
            campaign.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(campaign)
            
            campaign_dict = campaign_to_dict(campaign)
            return CampaignResponse(**campaign_dict)
        finally:
            db.close()
    
    async def delete_campaign(self, campaign_id: int, user_email: str) -> bool:
        """Delete campaign"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            return repo.delete_campaign(campaign_id, user_email)
        finally:
            db.close()
    
    async def analyze_campaign(self, campaign_id: int, user_email: str) -> Optional[CampaignResultsResponse]:
        """Run enhanced backlink analysis for a campaign using campaign-specific service"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            campaign = repo.get_campaign_by_id(campaign_id, user_email)
            if not campaign:
                return None
            
            # Convert to dict format for analysis service
            campaign_dict = campaign_to_dict(campaign)
            
            # Use enhanced campaign analysis service
            analysis_results = await campaign_analysis_service.analyze_campaign_comprehensive(
                campaign=campaign_dict,
                analysis_depth="standard"
            )
            
            # Store results in database
            if analysis_results.get("backlinks"):
                repo.add_backlink_results(campaign_id, analysis_results["backlinks"])
            
            # Convert to API response format
            campaign_response = CampaignResponse(**campaign_dict)
            api_response = campaign_analysis_service.convert_to_api_response(
                analysis_results=analysis_results,
                campaign=campaign_response
            )
            
            return CampaignResultsResponse(
                campaign=api_response["campaign"],
                results=api_response["results"],
                total_results=api_response["total_results"],
                verified_coverage=api_response["verified_coverage"],
                potential_coverage=api_response["potential_coverage"]
            )
        
        except Exception as e:
            print(f"Error analyzing campaign {campaign_id}: {str(e)}")
            # Fallback to basic analysis
            return await self._basic_campaign_analysis(campaign_id, user_email)
    
    async def _basic_campaign_analysis(self, campaign_id: int, user_email: str) -> Optional[CampaignResultsResponse]:
        """Fallback basic analysis using original implementation"""
        db = self._get_db_session()
        try:
            repo = CampaignRepository(db)
            campaign = repo.get_campaign_by_id(campaign_id, user_email)
            if not campaign:
                return None
            
            campaign_dict = campaign_to_dict(campaign)
            
            # Use existing link analysis service to get backlink data
            # Analyze campaign URL if provided, otherwise analyze domain
            target_url = campaign_dict.get("campaign_url") or f"https://{campaign_dict['client_domain']}"
            
            analysis_result = await self.link_analyzer.analyze_backlinks(
                target_url=target_url,
                mode="prefix",
                limit=100,
                offset=0,
                include_subdomains=True
            )
        
            # Convert backlinks to campaign results format
            results = []
            verified_count = 0
            potential_count = 0
            
            for backlink in analysis_result.backlinks:
                # Determine coverage status based on campaign criteria
                coverage_status = self._classify_coverage(backlink, campaign_dict)
                
                if coverage_status == "verified":
                    verified_count += 1
                else:
                    potential_count += 1
                
                result = BacklinkResultResponse(
                    id=len(results) + 1,
                    url=backlink.url_from,
                    page_title=backlink.title or "Unknown",
                    first_seen=backlink.first_seen,
                    coverage_status=coverage_status,
                    source_api="ahrefs",  # Based on our current implementation
                    domain_rating=backlink.domain_rating,
                    confidence_score="0.85"  # Placeholder confidence score
                )
                results.append(result)
            
            return CampaignResultsResponse(
                campaign=CampaignResponse(**campaign_dict),
                results=results,
                total_results=len(results),
                verified_coverage=verified_count,
                potential_coverage=potential_count
            )
        
        except Exception as e:
            print(f"Error in basic campaign analysis {campaign_id}: {str(e)}")
            return CampaignResultsResponse(
                campaign=CampaignResponse(**campaign_dict),
                results=[],
                total_results=0,
                verified_coverage=0,
                potential_coverage=0
            )
        finally:
            db.close()
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format"""
        # Basic domain validation
        if not domain or len(domain) < 3:
            return False
        
        # Remove protocol if present
        domain = domain.replace("https://", "").replace("http://", "")
        
        # Check for valid domain pattern
        parts = domain.split(".")
        return len(parts) >= 2 and all(part.strip() for part in parts)
    
    def _classify_coverage(self, backlink, campaign) -> str:
        """Classify backlink as verified or potential coverage"""
        # Implementation of coverage classification logic
        
        # Check if it's a direct link to campaign URL
        campaign_url = campaign.get("campaign_url", "")
        if campaign_url and campaign_url in backlink.url_to:
            return "verified"
        
        # Check launch date criteria
        launch_date = campaign.get("launch_date")
        if launch_date and backlink.first_seen:
            if backlink.first_seen <= launch_date:
                return "verified"
        
        # Check domain rating threshold (specification mentions >= 8)
        if backlink.domain_rating and backlink.domain_rating >= 8:
            return "verified"
        
        # Check against blacklisted domains
        blacklist_domains = campaign.get("blacklist_domains", [])
        for domain in blacklist_domains:
            if domain.lower() in backlink.url_from.lower():
                return "excluded"  # We'll filter these out
        
        # Default to potential coverage
        return "potential"

# Global service instance
campaign_service = CampaignService()
