"""Seed a few paused campaigns for frontend testing.

Usage (from backend directory):
  set PYTHONPATH=./app; python scripts/seed_paused_campaigns.py

Idempotent: skips creation if a campaign with same (client_name, campaign_name)
exists for the seed user.
"""
from __future__ import annotations
import os
import sys
from datetime import date
from typing import List, Tuple

# Ensure the backend root is importable so `import app...` works
BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.database import SessionLocal
from app.database.repository import CampaignRepository
from app.models.campaign import CampaignData


SEED_USER = os.getenv('SEED_USER_EMAIL', 'demo@linkdive.ai').lower()


PAUSED_CAMPAIGNS: List[CampaignData] = [
    CampaignData(
        user_email=SEED_USER,
        client_name="Acme Widgets",
        campaign_name="Q1 Press Outreach",
        client_domain="acme-widgets.example",
        campaign_url="https://acme-widgets.example/blog/q1-press-outreach",
        launch_date=date(2024, 1, 15),
        monitoring_status="Paused",
        serp_keywords=["Acme Widgets press", "Acme Widgets news"],
        verification_keywords=["Acme Widgets", "press outreach"],
        blacklist_domains=["facebook.com", "twitter.com"],
    ),
    CampaignData(
        user_email=SEED_USER,
        client_name="Globex Media",
        campaign_name="Podcast Launch",
        client_domain="globex.media",
        campaign_url="https://globex.media/podcast",
        launch_date=date(2023, 11, 2),
        monitoring_status="Paused",
        serp_keywords=["Globex podcast", "media podcast"],
        verification_keywords=["Globex", "podcast"],
        blacklist_domains=[],
    ),
    CampaignData(
        user_email=SEED_USER,
        client_name="Initech",
        campaign_name="TPS Report Study",
        client_domain="initech.example",
        campaign_url="https://initech.example/research/tps-report-study",
        launch_date=date(2022, 5, 23),
        monitoring_status="Paused",
        serp_keywords=["TPS reports", "office productivity study"],
        verification_keywords=["Initech", "TPS"],
        blacklist_domains=["pinterest.com"],
    ),
]


def seed_paused() -> None:
    db = SessionLocal()
    repo = CampaignRepository(db)
    created: List[Tuple[str, str]] = []
    skipped: List[Tuple[str, str]] = []
    try:
        existing = {(c.client_name, c.campaign_name) for c in repo.get_campaigns_by_user(SEED_USER)}
        for c in PAUSED_CAMPAIGNS:
            key = (c.client_name, c.campaign_name)
            if key in existing:
                skipped.append(key)
                continue
            repo.create_campaign(c)
            created.append(key)
        print(f"Seed paused complete. Created={len(created)} Skipped(existing)={len(skipped)}")
        if created:
            for k in created:
                print("  +", k[0], "-", k[1])
        if skipped:
            for k in skipped:
                print("  = (skipped)", k[0], "-", k[1])
    finally:
        db.close()


if __name__ == "__main__":
    seed_paused()
