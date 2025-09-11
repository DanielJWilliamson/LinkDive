"""Bulk analyze all campaigns for the demo/dev user.

Usage (from backend directory):
  set PYTHONPATH=./app; python bulk_analyze_all.py

Optional env vars:
  ANALYZE_USER_EMAIL=<email>  (defaults to demo@linkdive.ai)
  ANALYSIS_DEPTH=standard|deep (defaults to standard)

This script bypasses the HTTP layer and invokes the internal analysis service so it can
be used even if the API server is not running. Results persist to the database using
repository logic (upsert semantics). Safe to re-run; only new backlinks are inserted.
"""
from __future__ import annotations
import os
import sys
import asyncio
from typing import Dict, Any
from datetime import datetime

BACKEND_ROOT = os.path.dirname(__file__)
APP_ROOT = os.path.join(BACKEND_ROOT, 'app')
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from app.core.database import SessionLocal
from app.database.repository import CampaignRepository, campaign_to_dict
from app.services.campaign_analysis_service import campaign_analysis_service

USER = os.getenv('ANALYZE_USER_EMAIL', 'demo@linkdive.ai').lower()
DEPTH = os.getenv('ANALYSIS_DEPTH', 'standard')


async def analyze_single(campaign_dict: Dict[str, Any]):
    # Ensure user_email present for downstream persistence lookups
    campaign_dict['user_email'] = campaign_dict.get('user_email', USER)
    res = await campaign_analysis_service.analyze_campaign_comprehensive(campaign_dict, analysis_depth=DEPTH)
    summary = res.get('summary', {})
    return {
        'campaign_id': campaign_dict['id'],
        'name': campaign_dict['campaign_name'],
        'verified': summary.get('verified_count', 0),
        'potential': summary.get('potential_count', 0),
        'total': summary.get('total_results', 0),
        'steps': res.get('analysis_steps', []),
        'error': res.get('error')
    }


async def main():
    print(f"[bulk] Starting bulk analysis at {datetime.utcnow().isoformat()}Z depth={DEPTH} user={USER}")
    db = SessionLocal()
    try:
        repo = CampaignRepository(db)
        campaigns = repo.get_campaigns_by_user(USER)
        if not campaigns:
            print("[bulk] No campaigns found for user.")
            return 0
        summaries = []
        for c in campaigns:
            c_dict = campaign_to_dict(c)
            print(f"[bulk] Analyzing campaign {c.id} - {c.campaign_name}...")
            s = await analyze_single(c_dict)
            summaries.append(s)
            if s['error']:
                print(f"    -> ERROR: {s['error']}")
            else:
                print(f"    -> Verified={s['verified']} Potential={s['potential']} Total={s['total']} Steps={','.join(s['steps'])}")
        # Aggregate
        agg_verified = sum(s['verified'] for s in summaries if not s['error'])
        agg_potential = sum(s['potential'] for s in summaries if not s['error'])
        agg_total = sum(s['total'] for s in summaries if not s['error'])
        print("[bulk] --------------------------------------------------")
        print(f"[bulk] Aggregate: Verified={agg_verified} Potential={agg_potential} Total={agg_total}")
        print("[bulk] Done.")
        return len(summaries)
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(main())