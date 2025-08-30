"""
Database repository for campaign operations using SQLAlchemy models
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.database.database import get_db
from app.database.models import Campaign, CampaignKeyword, DomainBlacklist, BacklinkResult, SerpRanking
from app.models.campaign import CampaignData, CampaignSearchRequest

class CampaignRepository:
    """Database repository for campaign operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(self, campaign_data: CampaignData) -> Campaign:
        """Create a new campaign in the database"""
        db_campaign = Campaign(
            user_email=campaign_data.user_email,
            client_name=campaign_data.client_name,
            campaign_name=campaign_data.campaign_name,
            client_domain=campaign_data.client_domain,
            campaign_url=campaign_data.campaign_url,
            launch_date=campaign_data.launch_date,
            monitoring_status=campaign_data.monitoring_status,
            auto_pause_date=campaign_data.auto_pause_date
        )
        
        self.db.add(db_campaign)
        self.db.flush()  # Get the ID without committing
        
        # Add keywords
        for keyword in campaign_data.serp_keywords:
            keyword_obj = CampaignKeyword(
                campaign_id=db_campaign.id,
                keyword_type="serp",
                keyword=keyword
            )
            self.db.add(keyword_obj)
        
        for keyword in campaign_data.verification_keywords:
            keyword_obj = CampaignKeyword(
                campaign_id=db_campaign.id,
                keyword_type="verification",
                keyword=keyword
            )
            self.db.add(keyword_obj)
        
        # Add blacklist domains
        for domain in campaign_data.blacklist_domains:
            blacklist_obj = DomainBlacklist(
                campaign_id=db_campaign.id,
                domain=domain
            )
            self.db.add(blacklist_obj)
        
        self.db.commit()
        self.db.refresh(db_campaign)
        return db_campaign
    
    def get_campaign_by_id(self, campaign_id: int, user_email: str) -> Optional[Campaign]:
        """Get a campaign by ID and user email"""
        return self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).first()
    
    def get_campaigns_by_user(self, user_email: str) -> List[Campaign]:
        """Get all campaigns for a user"""
        return self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(Campaign.user_email == user_email).order_by(Campaign.created_at.desc()).all()
    
    def search_campaigns(self, request: CampaignSearchRequest) -> List[Campaign]:
        """Search campaigns with filters"""
        query = self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(Campaign.user_email == request.user_email)
        
        # Apply filters
        if request.client_name:
            query = query.filter(Campaign.client_name.ilike(f"%{request.client_name}%"))
        
        if request.campaign_name:
            query = query.filter(Campaign.campaign_name.ilike(f"%{request.campaign_name}%"))
        
        if request.monitoring_status:
            query = query.filter(Campaign.monitoring_status == request.monitoring_status)
        
        if request.date_from:
            query = query.filter(Campaign.launch_date >= request.date_from)
        
        if request.date_to:
            query = query.filter(Campaign.launch_date <= request.date_to)
        
        return query.order_by(Campaign.created_at.desc()).all()
    
    def update_campaign_status(self, campaign_id: int, user_email: str, status: str) -> bool:
        """Update campaign monitoring status"""
        result = self.db.query(Campaign).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).update({"monitoring_status": status, "updated_at": datetime.utcnow()})
        
        if result > 0:
            self.db.commit()
            return True
        return False
    
    def delete_campaign(self, campaign_id: int, user_email: str) -> bool:
        """Delete a campaign and all related data"""
        campaign = self.db.query(Campaign).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).first()
        
        if campaign:
            self.db.delete(campaign)
            self.db.commit()
            return True
        return False
    
    def add_backlink_results(self, campaign_id: int, results: List[Dict[str, Any]]) -> int:
        """Add backlink results for a campaign"""
        count = 0
        for result in results:
            db_result = BacklinkResult(
                campaign_id=campaign_id,
                url=result.get("url"),
                page_title=result.get("page_title"),
                first_seen=result.get("first_seen"),
                last_seen=result.get("last_seen"),
                coverage_status=result.get("coverage_status", "potential"),
                source_api=result.get("source_api", "unknown"),
                domain_rating=result.get("domain_rating"),
                confidence_score=result.get("confidence_score"),
                content_analysis=result.get("content_analysis")
            )
            self.db.add(db_result)
            count += 1
        
        if count > 0:
            self.db.commit()
        return count
    
    def get_backlink_results(self, campaign_id: int, user_email: str) -> List[BacklinkResult]:
        """Get backlink results for a campaign"""
        return self.db.query(BacklinkResult).join(Campaign).filter(
            and_(
                BacklinkResult.campaign_id == campaign_id,
                Campaign.user_email == user_email
            )
        ).order_by(BacklinkResult.created_at.desc()).all()
    
    def add_serp_rankings(self, campaign_id: int, rankings: List[Dict[str, Any]]) -> int:
        """Add SERP ranking results for a campaign"""
        count = 0
        for ranking in rankings:
            db_ranking = SerpRanking(
                campaign_id=campaign_id,
                keyword=ranking.get("keyword"),
                url=ranking.get("url"),
                position=ranking.get("position"),
                page_title=ranking.get("page_title"),
                check_date=ranking.get("check_date", date.today())
            )
            self.db.add(db_ranking)
            count += 1
        
        if count > 0:
            self.db.commit()
        return count
    
    def get_serp_rankings(self, campaign_id: int, user_email: str) -> List[SerpRanking]:
        """Get SERP rankings for a campaign"""
        return self.db.query(SerpRanking).join(Campaign).filter(
            and_(
                SerpRanking.campaign_id == campaign_id,
                Campaign.user_email == user_email
            )
        ).order_by(SerpRanking.check_date.desc()).all()
    
    def get_campaign_stats(self, campaign_id: int, user_email: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        campaign = self.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            return {}
        
        backlink_count = self.db.query(BacklinkResult).filter(
            BacklinkResult.campaign_id == campaign_id
        ).count()
        
        verified_count = self.db.query(BacklinkResult).filter(
            and_(
                BacklinkResult.campaign_id == campaign_id,
                BacklinkResult.coverage_status == "verified"
            )
        ).count()
        
        return {
            "total_backlinks": backlink_count,
            "verified_coverage": verified_count,
            "potential_coverage": backlink_count - verified_count,
            "verification_rate": (verified_count / backlink_count * 100) if backlink_count > 0 else 0
        }

def campaign_to_dict(campaign: Campaign) -> Dict[str, Any]:
    """Convert SQLAlchemy Campaign model to dictionary"""
    return {
        "id": campaign.id,
        "user_email": campaign.user_email,
        "client_name": campaign.client_name,
        "campaign_name": campaign.campaign_name,
        "client_domain": campaign.client_domain,
        "campaign_url": campaign.campaign_url,
        "launch_date": campaign.launch_date.isoformat() if campaign.launch_date else None,
        "monitoring_status": campaign.monitoring_status,
        "auto_pause_date": campaign.auto_pause_date.isoformat() if campaign.auto_pause_date else None,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        "serp_keywords": [k.keyword for k in campaign.keywords if k.keyword_type == "serp"],
        "verification_keywords": [k.keyword for k in campaign.keywords if k.keyword_type == "verification"],
        "blacklist_domains": [b.domain for b in campaign.blacklist_domains]
    }
