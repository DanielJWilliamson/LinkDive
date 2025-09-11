#!/usr/bin/env python3
"""
Add sample data to the LinkDive database for demonstration purposes
"""
import sys
import os
from datetime import datetime
from app.utils.datetime_utils import utc_now

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.database.models import Campaign, CampaignKeyword, BacklinkResult, SerpRanking
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

def create_sample_campaigns():
    """Create sample campaigns for demonstration."""
    db = SessionLocal()
    
    try:
        # Create sample campaigns
        campaigns = [
            Campaign(
                name="E-commerce SEO Campaign",
                target_domain="example-store.com",
                status="active",
                created_at=utc_now()
            ),
            Campaign(
                name="Tech Blog Outreach",
                target_domain="techblog-demo.com", 
                status="active",
                created_at=utc_now()
            ),
            Campaign(
                name="Local Business Boost",
                target_domain="localbiz-example.com",
                status="paused",
                created_at=utc_now()
            )
        ]
        
        for campaign in campaigns:
            db.add(campaign)
        
        db.commit()
        
        # Get the created campaigns to add keywords
        db_campaigns = db.query(Campaign).all()
        
        # Add keywords for each campaign
        keywords_data = [
            # E-commerce keywords
            {"campaign_id": db_campaigns[0].id, "keyword": "best online store", "search_volume": 1500, "difficulty": 65},
            {"campaign_id": db_campaigns[0].id, "keyword": "buy products online", "search_volume": 2200, "difficulty": 72},
            {"campaign_id": db_campaigns[0].id, "keyword": "e-commerce platform", "search_volume": 890, "difficulty": 58},
            
            # Tech blog keywords
            {"campaign_id": db_campaigns[1].id, "keyword": "programming tutorials", "search_volume": 3400, "difficulty": 45},
            {"campaign_id": db_campaigns[1].id, "keyword": "web development", "search_volume": 5600, "difficulty": 78},
            {"campaign_id": db_campaigns[1].id, "keyword": "coding best practices", "search_volume": 1200, "difficulty": 52},
            
            # Local business keywords
            {"campaign_id": db_campaigns[2].id, "keyword": "local services near me", "search_volume": 4500, "difficulty": 42},
            {"campaign_id": db_campaigns[2].id, "keyword": "small business solutions", "search_volume": 980, "difficulty": 55},
        ]
        
        for kw_data in keywords_data:
            keyword = CampaignKeyword(**kw_data)
            db.add(keyword)
        
        # Add some sample backlink results
        backlink_results = [
            BacklinkResult(
                campaign_id=db_campaigns[0].id,
                source_url="https://tech-review-site.com/best-stores",
                target_url="https://example-store.com",
                anchor_text="top online store",
                domain_authority=65,
                page_authority=58,
                status="live",
                found_date=utc_now()
            ),
            BacklinkResult(
                campaign_id=db_campaigns[1].id,
                source_url="https://developer-community.com/resources",
                target_url="https://techblog-demo.com/tutorials",
                anchor_text="programming guide",
                domain_authority=72,
                page_authority=68,
                status="live",
                found_date=utc_now()
            )
        ]
        
        for backlink in backlink_results:
            db.add(backlink)
        
        # Add some SERP ranking data
        serp_rankings = [
            SerpRanking(
                campaign_id=db_campaigns[0].id,
                keyword="best online store",
                url="https://example-store.com",
                position=12,
                search_engine="google",
                location="United States",
                checked_date=utc_now()
            ),
            SerpRanking(
                campaign_id=db_campaigns[1].id,
                keyword="programming tutorials",
                url="https://techblog-demo.com/tutorials",
                position=8,
                search_engine="google",
                location="United States",
                checked_date=utc_now()
            )
        ]
        
        for ranking in serp_rankings:
            db.add(ranking)
        
        db.commit()
        
        logger.info(f"Created {len(campaigns)} campaigns with keywords and sample data")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Create sample data for demonstration."""
    try:
        logger.info("Creating sample campaign data...")
        
        if create_sample_campaigns():
            logger.info("Sample data created successfully!")
            return True
        else:
            logger.error("Failed to create sample data")
            return False
            
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    else:
        print("✅ Sample campaign data created successfully!")
