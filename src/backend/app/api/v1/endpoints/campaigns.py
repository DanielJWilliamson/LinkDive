"""
Campaign management API endpoints
"""
from typing import List, Dict
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session

from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate, 
    CampaignResponse,
    CampaignResultsResponse,
    CampaignCoverageSummary,
    AggregateCoverageSummary
)
from app.core.database import get_db
from app.database.repository import CampaignRepository, campaign_to_dict
from app.services.campaign_service import campaign_service  # retained for other uses
from app.services.campaign_analysis_service import campaign_analysis_service
from app.core.metrics import metrics
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
from app.services.external.dataforseo_client import dataforseo_client
from app.services.background_processing_service import background_processing_service

router = APIRouter()

from app.core.auth import get_current_user
from app.utils.datetime_utils import utc_now

def normalize_campaign_payload(campaign_data: CampaignCreate) -> CampaignCreate:
    """Normalize inbound campaign creation payload (trim strings, drop empty array entries).

    IMPORTANT: Domain protocol removal happens only AFTER validation so we receive the original
    value to detect protocol misuse. Caller must run validate before this normalization.
    """
    cleaned = campaign_data.model_copy(deep=True)
    cleaned.client_name = cleaned.client_name.strip()
    cleaned.campaign_name = cleaned.campaign_name.strip()
    # Only canonicalize domain now (assumes validation already occurred)
    cleaned.client_domain = cleaned.client_domain.strip().replace('https://', '').replace('http://', '').rstrip('/')
    if cleaned.campaign_url:
        cleaned.campaign_url = cleaned.campaign_url.strip()
    cleaned.serp_keywords = sorted({k.strip() for k in cleaned.serp_keywords if k and k.strip()})
    cleaned.verification_keywords = sorted({k.strip() for k in cleaned.verification_keywords if k and k.strip()})
    cleaned.blacklist_domains = sorted({d.strip().lower() for d in cleaned.blacklist_domains if d and d.strip()})
    return cleaned


def validate_campaign_payload(campaign_data: CampaignCreate) -> Dict[str, str]:
    """Return dict of field_errors for invalid campaign payload values."""
    errors: Dict[str, str] = {}
    # Required string checks
    if not campaign_data.client_name.strip():
        errors["client_name"] = "Client name is required"
    if not campaign_data.campaign_name.strip():
        errors["campaign_name"] = "Campaign name is required"
    # Domain validation: simple hostname pattern (no protocol, at least one dot, allowed chars)
    import re
    domain = campaign_data.client_domain.strip()
    if not domain:
        errors["client_domain"] = "Client domain is required"
    else:
        pattern = re.compile(r"^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$")
        if domain.startswith("http://") or domain.startswith("https://"):
            errors["client_domain"] = "Domain must not include protocol"
        elif not pattern.match(domain):
            errors["client_domain"] = "Invalid domain format"
    # Launch date cannot be > today + 1 day buffer
    if campaign_data.launch_date and campaign_data.launch_date > (date.today()):
        # Allow only today or past; future launch scheduling handled elsewhere
        errors["launch_date"] = "Launch date cannot be in the future"
    return errors


def campaign_create_dependency(campaign_data: CampaignCreate = Body(...)) -> CampaignCreate:
    """Dependency to validate & normalize campaign creation payload.

    Separating this allows reuse (future bulk creation) and keeps the route lean.
    Performs validation first (to allow protocol detection) then normalization.
    Raises HTTP 422 with unified error schema on validation failure.
    """
    field_errors = validate_campaign_payload(campaign_data)
    normalized = normalize_campaign_payload(campaign_data)
    if field_errors:
        raise HTTPException(status_code=422, detail={
            "error": {
                "type": "VALIDATION_ERROR",
                "field_errors": field_errors
            }
        })
    return normalized


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate = Depends(campaign_create_dependency),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new PR campaign (validated & normalized via dependency)."""
    try:
        from app.models.campaign import CampaignData
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
        repo = CampaignRepository(db)
        db_campaign = repo.create_campaign(internal_data)
        campaign_dict = campaign_to_dict(db_campaign)
        return CampaignResponse(**campaign_dict)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": {"type": "VALUE_ERROR", "message": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"type": "FAILED_CREATE", "message": str(e)}})

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
    campaign.updated_at = utc_now()
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
    """Run backlink analysis for a campaign (direct path using analysis service)."""
    from time import perf_counter
    repo = CampaignRepository(db)
    campaign = repo.get_campaign_by_id(campaign_id, current_user)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign_dict = campaign_to_dict(campaign)
    # Inject user_email (already present) explicitly ensure analysis has it
    campaign_dict["user_email"] = current_user
    # Execute comprehensive analysis (handles persistence / upserts internally)
    t0 = perf_counter()
    analysis_results = await campaign_analysis_service.analyze_campaign_comprehensive(campaign_dict)
    duration = perf_counter() - t0
    metrics.inc("campaign_analyses_total")
    try:
        summary = analysis_results.get("summary", {})
        metrics.inc("backlinks_verified_added", summary.get("verified_count", 0))
        metrics.inc("backlinks_potential_added", summary.get("potential_count", 0))
        metrics.set_gauge("last_campaign_analysis_duration_seconds", duration)
    except Exception:
        pass
    # Re-fetch campaign to get updated last_backlink_fetch_at set during analysis
    try:
        # Use a fresh session to avoid stale identity map (update occurred in separate session inside analysis service)
        from app.core.database import get_db as _gd
        fresh_db = next(_gd())
        fresh_repo = CampaignRepository(fresh_db)
        refreshed = fresh_repo.get_campaign_by_id(campaign_id, current_user)
        if refreshed:
            campaign_dict = campaign_to_dict(refreshed)
    except Exception:
        pass
    from app.models.campaign import CampaignResponse, BacklinkResultResponse
    campaign_response = CampaignResponse(**campaign_dict)
    # Fetch cumulative stored backlink results & stats
    stored_results = repo.get_backlink_results(campaign_id, current_user)
    stats = repo.get_campaign_stats(campaign_id, current_user)
    result_responses = [
        BacklinkResultResponse(
            id=r.id,
            url=r.url,
            page_title=r.page_title,
            first_seen=r.first_seen,
            coverage_status=r.coverage_status,
            source_api=r.source_api,
            domain_rating=r.domain_rating,
            confidence_score=str(r.confidence_score) if r.confidence_score else None,
            link_destination=r.link_destination
        ) for r in stored_results
    ]
    return CampaignResultsResponse(
        campaign=campaign_response,
        results=result_responses,
        total_results=stats.get("total_backlinks", 0),
        verified_coverage=stats.get("verified_coverage", 0),
        potential_coverage=stats.get("potential_coverage", 0)
    )

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

@router.get("/campaigns/{campaign_id}/coverage", response_model=CampaignCoverageSummary)
async def get_campaign_coverage(
    campaign_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed coverage summary for a single campaign."""
    try:
        repo = CampaignRepository(db)
        detail = repo.get_campaign_coverage_detail(campaign_id, current_user)
        if not detail:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return CampaignCoverageSummary(**detail)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve coverage: {str(e)}")

@router.get("/coverage/summary", response_model=AggregateCoverageSummary)
async def get_aggregate_coverage(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregate coverage metrics across all campaigns for the current user."""
    try:
        repo = CampaignRepository(db)
        agg = repo.get_aggregate_coverage(current_user)
        return AggregateCoverageSummary(**agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve aggregate coverage: {str(e)}")

@router.get("/metrics", summary="Runtime metrics")
async def metrics_endpoint():
    """Return in-memory metrics snapshot."""
    snap = metrics.snapshot()
    return snap

@router.get("/health", summary="Application health")
async def health():
    """Basic health including last scheduler tick and worker status."""
    sched_tick = getattr(background_processing_service, 'last_scheduler_tick', None)
    # Lightweight DB ping
    db_ok = True
    try:
        from app.core.database import get_db as _gdb
        _db = next(_gdb())
        _db.execute("SELECT 1")
    except Exception:
        db_ok = False
    task_queue_depth = getattr(background_processing_service, 'task_queue', None).qsize() if getattr(background_processing_service, 'task_queue', None) else None
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "v1",
        "db": {"status": "up" if db_ok else "down"},
        "task_queue_depth": task_queue_depth,
        "last_scheduler_tick": sched_tick.isoformat() if sched_tick else None,
        "metrics": metrics.snapshot()
    }

@router.get("/campaigns/{campaign_id}/coverage/export")
async def export_campaign_coverage(
    campaign_id: int,
    status: str = "all",
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export campaign coverage as CSV (verified|all)."""
    repo = CampaignRepository(db)
    stats_detail = repo.get_campaign_coverage_detail(campaign_id, current_user)
    if not stats_detail:
        raise HTTPException(status_code=404, detail="Campaign not found")
    backlink_results = repo.get_backlink_results(campaign_id, current_user)
    # Prepare backlink rows
    rows = []
    for r in backlink_results:
        if status == 'verified' and r.coverage_status != 'verified':
            continue
        rows.append({
            'url': r.url,
            'coverage_status': r.coverage_status,
            'domain_rating': r.domain_rating,
            'link_destination': r.link_destination,
            'confidence_score': r.confidence_score,
            'first_seen': r.first_seen.isoformat() if r.first_seen else '',
        })
    # Add a summary sheet style first row (campaign level stats)
    summary_headers = [
        'campaign_id','campaign_name','client_domain','total_backlinks','verified_backlinks',
        'potential_backlinks','verification_rate'
    ]
    def generate():
        output = StringIO()
        # Write summary line
        writer_summary = csv.writer(output)
        writer_summary.writerow(summary_headers)
        writer_summary.writerow([
            stats_detail['campaign_id'],
            stats_detail['campaign_name'],
            stats_detail['client_domain'],
            stats_detail['total_backlinks'],
            stats_detail['verified_coverage'],
            stats_detail['potential_coverage'],
            f"{stats_detail['verification_rate']:.2f}",
        ])
        # Blank line separator
        output.write("\n")
        # Backlink detail section
        detail_fieldnames = list(rows[0].keys()) if rows else ['url','coverage_status']
        writer = csv.DictWriter(output, fieldnames=detail_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        yield output.getvalue()
    filename = f"campaign_{campaign_id}_coverage_{status}.csv"
    return StreamingResponse(generate(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.post("/campaigns/{campaign_id}/serp/ingest", summary="Trigger SERP ingestion for a single keyword")
async def trigger_serp_ingestion(
    campaign_id: int,
    keyword: str = Body(..., embed=True),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger SERP ingestion for a provided keyword (deterministic test helper).

    Returns the number of SERP ranking rows inserted and any new backlink candidates discovered.
    """
    repo = CampaignRepository(db)
    campaign = repo.get_campaign_by_id(campaign_id, current_user)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    # Fetch SERP results (mock if no credentials)
    serp_results = await dataforseo_client.fetch_serp(keyword, top_n=10)
    # Ingest results
    inserted = repo.ingest_serp_results(campaign_id, current_user, keyword, [
        {"url": r.url, "position": r.position, "page_title": r.page_title}
        for r in serp_results
    ])
    from app.core.metrics import metrics
    if inserted:
        metrics.inc("serp_ingestions")
    return {
        "campaign_id": campaign_id,
        "keyword": keyword,
        "serp_rankings_inserted": inserted,
        "mock_mode": True if not (dataforseo_client.username and dataforseo_client.password) else False
    }
