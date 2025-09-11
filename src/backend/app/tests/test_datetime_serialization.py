from datetime import datetime, UTC
import json
from app.models.backlink import Backlink, LinkType, BacklinkStatus
from app.models.analysis import QualityScore

def test_backlink_datetime_serialization():
    now = datetime.now(UTC)
    bl = Backlink(
        url_from="https://example.com/page",
        url_to="https://target.com",
        anchor_text="Example Anchor",
        first_seen=now,
        last_seen=now,
        link_type=LinkType.DOFOLLOW,
        status=BacklinkStatus.ACTIVE,
        data_source="ahrefs",
    )
    dumped = json.loads(bl.model_dump_json())
    # Ensure datetime fields serialized as ISO strings
    assert dumped["first_seen"].startswith(now.isoformat()[:19])
    assert dumped["last_seen"].startswith(now.isoformat()[:19])
    assert dumped["last_updated"].endswith("Z") or "T" in dumped["last_updated"]


def test_quality_score_datetime_serialization():
    now = datetime.now(UTC)
    qs = QualityScore(
        overall_score=90,
        domain_authority_score=85,
        relevance_score=88,
        diversity_score=80,
        velocity_score=75,
        natural_score=82,
        spam_risk_score=10,
        grade="A",
        strengths=["Strong DR"],
        weaknesses=["Limited diversity"],
        score_explanation="Well-balanced profile",
        confidence_level=95,
    )
    dumped = json.loads(qs.model_dump_json())
    assert dumped["calculated_at"].startswith(qs.calculated_at.isoformat()[:19])
