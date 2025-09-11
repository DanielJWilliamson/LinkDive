import csv
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _create_campaign():
    payload = {
        "client_name": "Test Co",
        "campaign_name": "Export",
        "client_domain": "example.org",
        "campaign_url": "https://example.org/launch",
        "serp_keywords": ["alpha"],
        "verification_keywords": ["Test"],
        "blacklist_domains": []
    }
    r = client.post("/api/campaigns", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_coverage_csv_export_basic_headers():
    campaign_id = _create_campaign()
    r = client.get(f"/api/campaigns/{campaign_id}/coverage/export")
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("text/csv")
    # Parse CSV content
    content = r.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert rows, "CSV should not be empty"
    header = rows[0]
    # Ensure core columns exist (flexible to future additions)
    for expected in ["campaign_id", "campaign_name", "total_backlinks", "verified_backlinks", "verification_rate"]:
        assert expected in header
