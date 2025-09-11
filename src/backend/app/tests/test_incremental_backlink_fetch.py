from fastapi.testclient import TestClient
from datetime import date
from app.main import app
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData

client = TestClient(app)


def _create_campaign(db):
    repo = CampaignRepository(db)
    c = CampaignData(
        user_email="demo@linkdive.ai",
        client_name="Client",
        campaign_name="Incremental",
        client_domain="example.com",
        campaign_url=None,
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=[],
        verification_keywords=[],
        blacklist_domains=[],
    )
    return repo.create_campaign(c)


def test_incremental_backlink_fetch_timestamp_and_filter():
    db = next(get_db())
    campaign = _create_campaign(db)
    # First analysis run should record timestamp and insert some backlinks
    r1 = client.post(f"/api/campaigns/{campaign.id}/analyze")
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    ts1 = data1["campaign"]["last_backlink_fetch_at"]
    assert ts1 is not None
    total1 = data1["total_results"]
    assert total1 > 0

    # Second run immediately should either yield zero new results OR not increase count (incremental filter)
    r2 = client.post(f"/api/campaigns/{campaign.id}/analyze")
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    ts2 = data2["campaign"]["last_backlink_fetch_at"]
    # Timestamp should advance (>=) and total results should not decrease
    assert ts2 is not None
    assert ts2 >= ts1
    assert data2["total_results"] >= total1
    # If providers return deterministic mock data with identical first_seen dates, incremental filter should skip duplicates, so total shouldn't balloon uncontrollably
    assert data2["total_results"] <= total1 + 5
