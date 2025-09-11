from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_detailed_health_includes_metrics():
    resp = client.get("/api/v1/health/detailed")
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert set(data["metrics"].keys()) == {"counters", "gauges", "timestamps"}
    # Services should include database status key
    assert "database" in data.get("services", {})