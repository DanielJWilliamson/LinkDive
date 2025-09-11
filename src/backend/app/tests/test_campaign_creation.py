import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from app.main import app

client = TestClient(app)

@pytest.fixture
def campaign_payload():
    return {
        "client_name": "  Acme  ",
        "campaign_name": "Launch  ",
        "client_domain": "example.com",
        "campaign_url": "https://example.com/blog/launch",
        "serp_keywords": ["keyword1", "keyword1", "  keyword2  ", ""],
        "verification_keywords": ["Acme", "Launch"],
        "blacklist_domains": ["spam.com", "Spam.com", " "]
    }

def test_campaign_creation_normalizes(campaign_payload):
    # Router mounted under /api as well; use /api/campaigns (campaigns router prefix)
    resp = client.post("/api/campaigns", json=campaign_payload, headers={"X-User-Email": "demo@linkdive.ai"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["client_domain"] == "example.com"
    assert data["client_name"] == "Acme"  # trimmed
    assert data["campaign_name"] == "Launch"  # trimmed
    # Arrays deduped & cleaned
    assert data["serp_keywords"] == ["keyword1", "keyword2"]
    assert data["blacklist_domains"] == ["spam.com"]

def test_campaign_invalid_domain_protocol():
    payload = {
        "client_name": "Acme",
        "campaign_name": "Launch",
        "client_domain": "http://bad-domain.com",
    }
    resp = client.post("/api/campaigns", json=payload, headers={"X-User-Email": "demo@linkdive.ai"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error"]["field_errors"]["client_domain"] == "Domain must not include protocol"

def test_campaign_future_launch_date_rejected():
    future = (date.today() + timedelta(days=2)).isoformat()
    payload = {
        "client_name": "Acme",
        "campaign_name": "Launch",
        "client_domain": "example.com",
        "launch_date": future
    }
    resp = client.post("/api/campaigns", json=payload, headers={"X-User-Email": "demo@linkdive.ai"})
    assert resp.status_code == 422
    body = resp.json()
    assert "launch_date" in body["detail"]["error"]["field_errors"]

def test_campaign_empty_arrays_cleaned():
    payload = {
        "client_name": "Acme",
        "campaign_name": "Launch",
        "client_domain": "example.com",
        "serp_keywords": ["", "  "],
        "verification_keywords": [""],
        "blacklist_domains": [""],
    }
    resp = client.post("/api/campaigns", json=payload, headers={"X-User-Email": "demo@linkdive.ai"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["serp_keywords"] == []
    assert data["verification_keywords"] == []
    assert data["blacklist_domains"] == []

