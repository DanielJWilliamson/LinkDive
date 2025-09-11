"""Seed realistic campaigns derived from the specification (Info.txt).

Usage (from backend directory):
  set PYTHONPATH=./app; python seed_campaigns_from_spec.py

Creates multiple campaigns for the demo/dev user (demo@linkdive.ai unless X-User-Email enforced)
so the frontend dashboard immediately shows content and analyses can be triggered.

Idempotent: skips creation if a campaign with same (client_name, campaign_name) already exists
for the demo user.
"""
from __future__ import annotations
import os
import sys
from datetime import date
from typing import List, Tuple

# Ensure app package importable when script executed directly
BACKEND_ROOT = os.path.dirname(__file__)
APP_ROOT = os.path.join(BACKEND_ROOT, 'app')
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from app.core.database import SessionLocal
from app.database.models import Campaign, CampaignKeyword, DomainBlacklist
from app.utils.datetime_utils import utc_now
from app.models.campaign import CampaignData
from app.database.repository import CampaignRepository

DEMO_USER = os.getenv('SEED_USER_EMAIL', 'demo@linkdive.ai').lower()

SPEC_CAMPAIGNS: List[CampaignData] = [
    CampaignData(
        user_email=DEMO_USER,
        client_name="Chill.ie",
        campaign_name="Most Affordable Homes",
        client_domain="chill.ie",
        campaign_url="https://www.chill.ie/blog/the-counties-with-the-most-affordable-homes/",
        launch_date=date(2022,1,21),
        serp_keywords=[
            "Most Affordable Homes Chill.ie",
            "affordable homes Ireland",
            "cheapest counties to buy a house Ireland",
            "Chill Insurance housing study"
        ],
        verification_keywords=[
            "Most Affordable Homes",
            "Chill.ie",
            "Chill Insurance",
            "cheapest counties",
            "affordable homes",
            "cost of living",
            "housing Ireland"
        ],
        blacklist_domains=[]
    ),
    # Additional illustrative campaign (different domain with mock data):
    CampaignData(
        user_email=DEMO_USER,
        client_name="OpenAI",
        campaign_name="AI Research Milestones",
        client_domain="openai.com",
        campaign_url="https://www.openai.com/",
        launch_date=date(2024,5,15),
        serp_keywords=[
            "OpenAI research milestones",
            "ChatGPT innovation",
            "OpenAI breakthrough",
            "AI research OpenAI"
        ],
        verification_keywords=[
            "OpenAI",
            "ChatGPT",
            "AI research",
            "language model"
        ],
        blacklist_domains=["facebook.com"]
    ),
    CampaignData(
        user_email=DEMO_USER,
        client_name="Example Corp",
        campaign_name="Reference Domain Awareness",
        client_domain="example.com",
        campaign_url="https://www.example.com/",
        launch_date=date(2023,9,10),
        serp_keywords=[
            "example domain reference",
            "IANA example domain",
            "placeholder domain"
        ],
        verification_keywords=["example.com", "example domain", "placeholder"],
        blacklist_domains=[]
    )
]


def seed():
    db = SessionLocal()
    repo = CampaignRepository(db)
    created: List[Tuple[str,str]] = []
    skipped: List[Tuple[str,str]] = []
    try:
        existing = {(c.client_name, c.campaign_name) for c in repo.get_campaigns_by_user(DEMO_USER)}
        for campaign in SPEC_CAMPAIGNS:
            key = (campaign.client_name, campaign.campaign_name)
            if key in existing:
                skipped.append(key)
                continue
            repo.create_campaign(campaign)
            created.append(key)
        print(f"Seed complete. Created={len(created)} Skipped(existing)={len(skipped)}")
        if created:
            for c in created:
                print("  +", c[0], "-", c[1])
        if skipped:
            for c in skipped:
                print("  = (skipped)", c[0], "-", c[1])
    finally:
        db.close()


if __name__ == "__main__":
    seed()