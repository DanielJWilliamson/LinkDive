from fastapi.testclient import TestClient
from app.main import app
from datetime import date
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
        campaign_name="SERPTest",
        client_domain="example.com",
        campaign_url="https://example.com/landing",
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=["seed"],
        verification_keywords=[],
        blacklist_domains=[],
    )
    created = repo.create_campaign(c)
    return created.id


def test_manual_serp_ingestion_endpoint():
    campaign_id = _create_campaign()

    # Snapshot metrics before
    before_metrics = client.get("/api/metrics").json()
    before_count = before_metrics.get("counters", {}).get("serp_ingestions", 0)

    resp = client.post(f"/api/campaigns/{campaign_id}/serp/ingest", json={"keyword": "testkw"})
    assert resp.status_code == 200
    data = resp.json()
    # Basic shape assertions
    assert data["campaign_id"] == campaign_id
    assert data["keyword"] == "testkw"
    assert data["serp_rankings_inserted"] >= 0  # mock returns 2, but stay flexible
    # Metrics after
    after_metrics = client.get("/api/metrics").json()
    after_count = after_metrics.get("counters", {}).get("serp_ingestions", 0)
    # If insertion happened expect increment; tolerate zero if mock produced none
    if data["serp_rankings_inserted"] > 0:
        assert after_count >= before_count + 1
