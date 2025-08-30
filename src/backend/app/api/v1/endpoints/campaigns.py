"""
Campaign management API endpoints
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate, 
    CampaignResponse,
    CampaignResultsResponse
)
from app.core.database import get_db
from app.database.repository import CampaignRepository, campaign_to_dict
from app.services.campaign_service import campaign_service

router = APIRouter()

# Temporary user authentication (replace with real Google OAuth)
def get_current_user() -> str:
    """
    Temporary function to get current user email
    In production, this would validate Google OAuth token and extract user email
    For now, we'll use a hardcoded linkdive.ai email
    """
    return "demo@linkdive.ai"

@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new PR campaign"""
    try:
        # Convert Pydantic model to our internal format
        from app.models.campaign import CampaignData
        from datetime import date
        
        internal_data = CampaignData(
            user_email=current_user,
            client_name=campaign_data.client_name,
            campaign_name=campaign_data.campaign_name,
            client_domain=campaign_data.client_domain,
            campaign_url=campaign_data.campaign_url,
            launch_date=campaign_data.launch_date or date.today(),
            monitoring_status="Live",
            serp_keywords=campaign_data.serp_keywords,
            verification_keywords=campaign_data.verification_keywords,
            blacklist_domains=campaign_data.blacklist_domains or []
        )
        
        # Create campaign in database
        repo = CampaignRepository(db)
        db_campaign = repo.create_campaign(internal_data)
        
        # Convert to response format
        campaign_dict = campaign_to_dict(db_campaign)
        return CampaignResponse(**campaign_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for the current user"""
    try:
        repo = CampaignRepository(db)
        campaigns = repo.get_campaigns_by_user(current_user)
        return [CampaignResponse(**campaign_to_dict(campaign)) for campaign in campaigns]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaigns: {str(e)}")

@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific campaign"""
    repo = CampaignRepository(db)
    campaign = repo.get_campaign_by_id(campaign_id, current_user)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse(**campaign_to_dict(campaign))

@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    update_data: CampaignUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a campaign"""
    repo = CampaignRepository(db)
    
    # Get existing campaign
    campaign = repo.get_campaign_by_id(campaign_id, current_user)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(campaign, field):
            setattr(campaign, field, value)
    
    # Update timestamp
    campaign.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    
    return CampaignResponse(**campaign_to_dict(campaign))

@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    repo = CampaignRepository(db)
    success = repo.delete_campaign(campaign_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")

@router.post("/campaigns/{campaign_id}/analyze", response_model=CampaignResultsResponse)
async def analyze_campaign(
    campaign_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run backlink analysis for a campaign"""
    try:
        repo = CampaignRepository(db)
        
        # Get campaign
        campaign = repo.get_campaign_by_id(campaign_id, current_user)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Run analysis using the campaign service (which will store results in database)
        results = await campaign_service.analyze_campaign(campaign_id, current_user)
        if not results:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/campaigns/{campaign_id}/results", response_model=CampaignResultsResponse)
async def get_campaign_results(
    campaign_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get existing campaign analysis results"""
    try:
        repo = CampaignRepository(db)
        
        # Get campaign
        campaign = repo.get_campaign_by_id(campaign_id, current_user)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get stored results
        backlink_results = repo.get_backlink_results(campaign_id, current_user)
        stats = repo.get_campaign_stats(campaign_id, current_user)
        
        # Convert to response format
        campaign_dict = campaign_to_dict(campaign)
        campaign_response = CampaignResponse(**campaign_dict)
        
        # Convert backlink results
        from app.models.campaign import BacklinkResultResponse
        result_responses = []
        for result in backlink_results:
            result_responses.append(BacklinkResultResponse(
                id=result.id,
                url=result.url,
                page_title=result.page_title,
                first_seen=result.first_seen,
                coverage_status=result.coverage_status,
                source_api=result.source_api,
                domain_rating=result.domain_rating,
                confidence_score=str(result.confidence_score) if result.confidence_score else None
            ))
        
        return CampaignResultsResponse(
            campaign=campaign_response,
            results=result_responses,
            total_results=stats.get("total_backlinks", 0),
            verified_coverage=stats.get("verified_coverage", 0),
            potential_coverage=stats.get("potential_coverage", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")
