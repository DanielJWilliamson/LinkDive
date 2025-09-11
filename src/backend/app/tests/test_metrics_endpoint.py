from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_snapshot_structure():
    resp = client.get("/api/metrics")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Basic structural expectations
    assert "counters" in data
    assert "gauges" in data
    assert "timestamps" in data
    # Counters may be empty initially but should be a dict
    assert isinstance(data["counters"], dict)
    assert isinstance(data["gauges"], dict)
    assert isinstance(data["timestamps"], dict)
