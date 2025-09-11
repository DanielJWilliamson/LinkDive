from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData
from datetime import date

client = TestClient(app)

def create_campaign_direct(db):
    repo = CampaignRepository(db)
    c = CampaignData(
        user_email="demo@linkdive.ai",
        client_name="Client",
        campaign_name="Test",
        client_domain="example.com",
        campaign_url="https://example.com/blog/post",
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=[],
        verification_keywords=[],
        blacklist_domains=[]
    )
    return repo.create_campaign(c)

def test_duplicate_backlinks_skip():
    # Create campaign via repository directly
    db = next(get_db())
    campaign = create_campaign_direct(db)

    payload = [
        {"url": "https://news.example.com/article", "coverage_status": "potential", "source_api": "ahrefs"},
        {"url": "https://news.example.com/article", "coverage_status": "potential", "source_api": "ahrefs"},  # duplicate
    ]
    repo = CampaignRepository(db)
    inserted = repo.add_backlink_results(campaign.id, payload)
    assert inserted == 1

    # Verify link_destination classification
    payload2 = [{"url": "https://example.com/blog/post", "coverage_status": "verified", "source_api": "ahrefs"}]
    repo.add_backlink_results(campaign.id, payload2)
    # Query back
    results = repo.get_backlink_results(campaign.id, campaign.user_email)
    destinations = {r.url: r.link_destination for r in results}
    assert destinations.get("https://example.com/blog/post") == "blog_page"
