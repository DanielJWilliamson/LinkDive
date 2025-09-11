from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData
from datetime import date

client = TestClient(app)


def _create_campaign_for_user(user_email: str):
    db = next(get_db())
    repo = CampaignRepository(db)
    c = CampaignData(
        user_email=user_email,
        client_name="Client",
        campaign_name="AuthTest",
        client_domain="example.com",
        campaign_url="https://example.com/page",
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=[],
        verification_keywords=[],
        blacklist_domains=[]
    )
    return repo.create_campaign(c).id


def test_missing_header_uses_legacy_fallback_in_debug():
    # In debug mode the fallback should still work (returns list, maybe empty)
    resp = client.get("/api/campaigns")
    assert resp.status_code == 200


def test_header_overrides_user_identity():
    special_user = "override@example.org"
    cid = _create_campaign_for_user(special_user)
    resp = client.get(f"/api/campaigns/{cid}", headers={"X-User-Email": special_user})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_email"] == special_user
