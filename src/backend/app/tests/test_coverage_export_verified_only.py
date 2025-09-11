from fastapi.testclient import TestClient
from datetime import date
from app.main import app
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData
import csv
import io

client = TestClient(app)


def _create_campaign():
    db = next(get_db())
    repo = CampaignRepository(db)
    c = CampaignData(
        user_email="demo@linkdive.ai",
        client_name="Client",
        campaign_name="ExportTest",
        client_domain="example.com",
        campaign_url="https://example.com/page",
        launch_date=date.today(),
        monitoring_status="Live",
        serp_keywords=[],
        verification_keywords=[],
        blacklist_domains=[]
    )
    created = repo.create_campaign(c)
    # Add backlinks (one verified, one potential)
    repo.add_backlink_results(created.id, [
        {"url": "https://site-a.com/post", "coverage_status": "verified", "source_api": "ahrefs"},
        {"url": "https://site-b.com/post", "coverage_status": "potential", "source_api": "ahrefs"},
    ])
    return created.id


def test_verified_only_export_filters_rows():
    cid = _create_campaign()
    resp = client.get(f"/api/campaigns/{cid}/coverage/export", params={"status": "verified"})
    assert resp.status_code == 200
    content = resp.text
    # Parse CSV segments
    lines = [l for l in content.splitlines() if l.strip() != ""]
    # First non-empty line is summary header, second is summary data, third should be detail header
    assert len(lines) >= 3
    detail_header_index = 2  # after summary header and summary row
    detail_headers = lines[detail_header_index].split(',')
    # Remaining lines after header are detail rows
    detail_rows = lines[detail_header_index + 1:]
    # Ensure only verified rows present
    for row in detail_rows:
        parts = row.split(',')
        if 'coverage_status' in detail_headers:
            status_idx = detail_headers.index('coverage_status')
            assert parts[status_idx] == 'verified'
    # At least one verified row exported
    assert detail_rows, "No detail rows found in verified-only export"