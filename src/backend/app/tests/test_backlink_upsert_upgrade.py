from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData

client = TestClient(app)


def _create_campaign():
    db = next(get_db())
    repo = CampaignRepository(db)
    c = CampaignData(
        user_email="demo@linkdive.ai",
        client_name="Client",
        campaign_name="UpsertUpgrade",
        client_domain="example.com",
        campaign_url=None,
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=[],
        verification_keywords=[],
        blacklist_domains=[],
    )
    return repo.create_campaign(c)


def test_coverage_status_upgrades_and_last_seen_extends():
    campaign = _create_campaign()
    db = next(get_db())
    repo = CampaignRepository(db)
    url = "https://example.com/blog/post-a"

    # Initial insert as potential with earlier dates
    first_seen = date.today() - timedelta(days=2)
    last_seen = date.today() - timedelta(days=2)
    repo.add_backlink_results(campaign.id, [
        {"url": url, "coverage_status": "potential", "source_api": "ahrefs", "first_seen": first_seen, "last_seen": last_seen}
    ])

    # Upsert with verified + newer last_seen
    newer_last_seen = date.today()
    repo.add_backlink_results(campaign.id, [
        {"url": url, "coverage_status": "verified", "source_api": "ahrefs", "first_seen": date.today() - timedelta(days=1), "last_seen": newer_last_seen}
    ])

    # Fetch and assert upgrade
    rows = repo.get_backlink_results(campaign.id, campaign.user_email)
    target = [r for r in rows if r.url == url][0]
    assert target.coverage_status == "verified"
    assert target.first_seen == first_seen  # earliest preserved
    assert target.last_seen == newer_last_seen  # extended
