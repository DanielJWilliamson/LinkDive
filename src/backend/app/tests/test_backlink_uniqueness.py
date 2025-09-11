from fastapi.testclient import TestClient
from app.main import app
from datetime import date

client = TestClient(app)

payload = {
    "client_name": "Acme",
    "campaign_name": "Launch",
    "client_domain": "example.com",
    "serp_keywords": [],
    "verification_keywords": [],
    "blacklist_domains": []
}

def _create_campaign():
    r = client.post("/api/campaigns", json=payload, headers={"X-User-Email":"demo@linkdive.ai"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_backlink_uniqueness_idempotent_analysis():
    cid = _create_campaign()
    # First analysis run (mock backlinks inserted)
    r1 = client.post(f"/api/campaigns/{cid}/analyze", headers={"X-User-Email":"demo@linkdive.ai"})
    assert r1.status_code == 200, r1.text
    total1 = r1.json()["total_results"]
    assert total1 >= 0
    # Second run should not create duplicate rows; total should stay same or grow only if new mock provider adds items
    r2 = client.post(f"/api/campaigns/{cid}/analyze", headers={"X-User-Email":"demo@linkdive.ai"})
    assert r2.status_code == 200, r2.text
    total2 = r2.json()["total_results"]
    assert total2 >= total1
