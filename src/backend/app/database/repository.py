"""
Database repository for campaign operations using SQLAlchemy models
"""
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, exc, func, case
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.database import get_db
from app.database.models import Campaign, CampaignKeyword, DomainBlacklist, BacklinkResult, SerpRanking
from app.models.campaign import CampaignData, CampaignSearchRequest

class CampaignRepository:
    """Database repository for campaign operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(self, campaign_data: CampaignData) -> Campaign:
        """Create a new campaign in the database"""
        db_campaign = Campaign(
            user_email=campaign_data.user_email,
            client_name=campaign_data.client_name,
            campaign_name=campaign_data.campaign_name,
            client_domain=campaign_data.client_domain,
            campaign_url=campaign_data.campaign_url,
            launch_date=campaign_data.launch_date,
            monitoring_status=campaign_data.monitoring_status,
            auto_pause_date=campaign_data.auto_pause_date
        )
        
        self.db.add(db_campaign)
        self.db.flush()  # Get the ID without committing
        
        # Add keywords
        for keyword in campaign_data.serp_keywords:
            keyword_obj = CampaignKeyword(
                campaign_id=db_campaign.id,
                keyword_type="serp",
                keyword=keyword
            )
            self.db.add(keyword_obj)
        
        for keyword in campaign_data.verification_keywords:
            keyword_obj = CampaignKeyword(
                campaign_id=db_campaign.id,
                keyword_type="verification",
                keyword=keyword
            )
            self.db.add(keyword_obj)
        
        # Add blacklist domains
        for domain in campaign_data.blacklist_domains:
            blacklist_obj = DomainBlacklist(
                campaign_id=db_campaign.id,
                domain=domain
            )
            self.db.add(blacklist_obj)
        
        self.db.commit()
        self.db.refresh(db_campaign)
        return db_campaign
    
    def get_campaign_by_id(self, campaign_id: int, user_email: str) -> Optional[Campaign]:
        """Get a campaign by ID and user email"""
        return self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).first()
    
    def get_campaigns_by_user(self, user_email: str) -> List[Campaign]:
        """Get all campaigns for a user"""
        return self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(Campaign.user_email == user_email).order_by(Campaign.created_at.desc()).all()
    
    def search_campaigns(self, request: CampaignSearchRequest) -> List[Campaign]:
        """Search campaigns with filters"""
        query = self.db.query(Campaign).options(
            joinedload(Campaign.keywords),
            joinedload(Campaign.blacklist_domains)
        ).filter(Campaign.user_email == request.user_email)
        
        # Apply filters
        if request.client_name:
            query = query.filter(Campaign.client_name.ilike(f"%{request.client_name}%"))
        
        if request.campaign_name:
            query = query.filter(Campaign.campaign_name.ilike(f"%{request.campaign_name}%"))
        
        if request.monitoring_status:
            query = query.filter(Campaign.monitoring_status == request.monitoring_status)
        
        if request.date_from:
            query = query.filter(Campaign.launch_date >= request.date_from)
        
        if request.date_to:
            query = query.filter(Campaign.launch_date <= request.date_to)
        
        return query.order_by(Campaign.created_at.desc()).all()
    
    def update_campaign_status(self, campaign_id: int, user_email: str, status: str) -> bool:
        """Update campaign monitoring status"""
        result = self.db.query(Campaign).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).update({"monitoring_status": status, "updated_at": datetime.now(timezone.utc)})
        
        if result > 0:
            self.db.commit()
            return True
        return False
    
    def delete_campaign(self, campaign_id: int, user_email: str) -> bool:
        """Delete a campaign and all related data"""
        campaign = self.db.query(Campaign).filter(
            and_(Campaign.id == campaign_id, Campaign.user_email == user_email)
        ).first()
        
        if campaign:
            self.db.delete(campaign)
            self.db.commit()
            return True
        return False
    
    def add_backlink_results(self, campaign_id: int, results: List[Dict[str, Any]]) -> int:
        """Add backlink results for a campaign with database-level upsert.

        Behaviour:
          - New rows inserted.
          - Existing (campaign_id, url, source_api) rows have last_seen updated to the
            greatest(current, incoming) and updated_at touched.
          - coverage_status is *upgraded* to 'verified' if the incoming row is verified
            (never downgraded from verified to potential).
          - domain_rating / confidence_score updated if incoming provides a non-null value.
          - link_destination set if previously null.

        Return value matches previous implementation: count of *newly inserted* rows
        (not number of updates) so existing tests remain stable.
        """
        if not results:
            return 0

        # Load campaign domain once for destination classification.
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        domain = campaign.client_domain.lower().rstrip('/') if campaign and campaign.client_domain else ''

        # Preload existing keys to preserve return semantics for tests relying on skip count.
        existing_pairs: Set[Tuple[str, str]] = {
            (r.url, r.source_api)
            for r in self.db.query(BacklinkResult.url, BacklinkResult.source_api)
            .filter(BacklinkResult.campaign_id == campaign_id)
            .all()
        }

        payload: List[Dict[str, Any]] = []
        new_count = 0
        today = date.today()
        for r in results:
            url = r.get('url')
            if not url:
                continue
            source_api = r.get('source_api', 'unknown')
            key = (url, source_api)
            if key not in existing_pairs:
                new_count += 1
            # Classify destination (ensure consistent across inserts & updates)
            link_destination = None
            lower_url = url.lower()
            if domain and domain in lower_url:
                trimmed = lower_url.rstrip('/')
                if '/blog' in trimmed:
                    link_destination = 'blog_page'
                elif trimmed in {f'https://{domain}', f'http://{domain}', domain}:
                    link_destination = 'homepage'
                else:
                    link_destination = 'other'
            first_seen = r.get('first_seen') or today
            last_seen = r.get('last_seen') or first_seen
            payload.append({
                'campaign_id': campaign_id,
                'url': url,
                'page_title': r.get('page_title'),
                'first_seen': first_seen,
                'last_seen': last_seen,
                'coverage_status': r.get('coverage_status', 'potential'),
                'source_api': source_api,
                'domain_rating': r.get('domain_rating'),
                'confidence_score': r.get('confidence_score'),
                'content_analysis': r.get('content_analysis'),
                'link_destination': link_destination,
            })

        # Decide dialect-specific insert for ON CONFLICT.
        dialect = self.db.bind.dialect.name if self.db.bind else ''
        stmt = None
        conflict_cols = ['campaign_id', 'url', 'source_api']
        try:
            if dialect == 'postgresql':
                stmt = pg_insert(BacklinkResult).values(payload)
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_cols,
                    set={
                        # keep earliest first_seen
                        'first_seen': func.LEAST(BacklinkResult.first_seen, stmt.excluded.first_seen),
                        'last_seen': func.GREATEST(BacklinkResult.last_seen, stmt.excluded.last_seen),
                        'coverage_status': case(
                            (BacklinkResult.coverage_status == 'verified', BacklinkResult.coverage_status),
                            else_=stmt.excluded.coverage_status,
                        ),
                        'domain_rating': func.COALESCE(stmt.excluded.domain_rating, BacklinkResult.domain_rating),
                        'confidence_score': func.COALESCE(stmt.excluded.confidence_score, BacklinkResult.confidence_score),
                        'content_analysis': func.COALESCE(stmt.excluded.content_analysis, BacklinkResult.content_analysis),
                        'link_destination': func.COALESCE(BacklinkResult.link_destination, stmt.excluded.link_destination),
                        'updated_at': func.now(),
                    },
                )
            elif dialect == 'sqlite':
                stmt = sqlite_insert(BacklinkResult).values(payload)
                # SQLite: use excluded alias 'excluded'
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_cols,
                    set={
                        'first_seen': func.min(BacklinkResult.first_seen, stmt.excluded.first_seen),  # earliest
                        'last_seen': func.max(BacklinkResult.last_seen, stmt.excluded.last_seen),
                        'coverage_status': case(
                            (BacklinkResult.coverage_status == 'verified', BacklinkResult.coverage_status),
                            else_=stmt.excluded.coverage_status,
                        ),
                        'domain_rating': func.COALESCE(stmt.excluded.domain_rating, BacklinkResult.domain_rating),
                        'confidence_score': func.COALESCE(stmt.excluded.confidence_score, BacklinkResult.confidence_score),
                        'content_analysis': func.COALESCE(stmt.excluded.content_analysis, BacklinkResult.content_analysis),
                        'link_destination': func.COALESCE(BacklinkResult.link_destination, stmt.excluded.link_destination),
                        'updated_at': func.now(),
                    },
                )
            else:
                # Fallback: legacy per-row logic
                raise RuntimeError('dialect_fallback')

            self.db.execute(stmt)
            self.db.commit()
        except Exception:
            # Fallback path (legacy) on any failure to ensure ingestion still works.
            self.db.rollback()
            legacy_inserts = 0
            existing_pairs = existing_pairs  # already loaded
            for row in payload:
                key = (row['url'], row['source_api'])
                existing = self.db.query(BacklinkResult).filter(
                    BacklinkResult.campaign_id == campaign_id,
                    BacklinkResult.url == row['url'],
                    BacklinkResult.source_api == row['source_api']
                ).first() if key in existing_pairs else None
                if existing:
                    # Upgrade semantics
                    if existing.coverage_status != 'verified' and row['coverage_status'] == 'verified':
                        existing.coverage_status = 'verified'
                    # Preserve earliest first_seen
                    if row['first_seen'] and existing.first_seen and row['first_seen'] < existing.first_seen:
                        existing.first_seen = row['first_seen']
                    # Extend last_seen
                    if row['last_seen'] and (not existing.last_seen or row['last_seen'] > existing.last_seen):
                        existing.last_seen = row['last_seen']
                    # Fill nullable fields
                    if row.get('domain_rating') is not None:
                        existing.domain_rating = row['domain_rating']
                    if row.get('confidence_score') is not None:
                        existing.confidence_score = row['confidence_score']
                    if row.get('content_analysis') and not existing.content_analysis:
                        existing.content_analysis = row['content_analysis']
                    if row.get('link_destination') and not existing.link_destination:
                        existing.link_destination = row['link_destination']
                    continue
                # New row path
                try:
                    self.db.add(BacklinkResult(**row))
                    self.db.flush()
                    existing_pairs.add(key)
                    legacy_inserts += 1
                except exc.IntegrityError:
                    self.db.rollback()
                    continue
            if legacy_inserts:
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
            # Ensure new_count reflects actual inserts in fallback mode
            new_count = legacy_inserts
        return new_count
    
    def get_backlink_results(self, campaign_id: int, user_email: str) -> List[BacklinkResult]:
        """Get backlink results for a campaign"""
        return self.db.query(BacklinkResult).join(Campaign).filter(
            and_(
                BacklinkResult.campaign_id == campaign_id,
                Campaign.user_email == user_email
            )
        ).order_by(BacklinkResult.created_at.desc()).all()
    
    def add_serp_rankings(self, campaign_id: int, rankings: List[Dict[str, Any]]) -> int:
        """Add SERP ranking results for a campaign"""
        count = 0
        for ranking in rankings:
            db_ranking = SerpRanking(
                campaign_id=campaign_id,
                keyword=ranking.get("keyword"),
                url=ranking.get("url"),
                position=ranking.get("position"),
                page_title=ranking.get("page_title"),
                check_date=ranking.get("check_date", date.today())
            )
            self.db.add(db_ranking)
            count += 1
        
        if count > 0:
            self.db.commit()
        return count
    
    def get_serp_rankings(self, campaign_id: int, user_email: str) -> List[SerpRanking]:
        """Get SERP rankings for a campaign"""
        return self.db.query(SerpRanking).join(Campaign).filter(
            and_(
                SerpRanking.campaign_id == campaign_id,
                Campaign.user_email == user_email
            )
        ).order_by(SerpRanking.check_date.desc()).all()

    def ingest_serp_results(self, campaign_id: int, user_email: str, keyword: str, serp_results: List[Dict[str, Any]]) -> int:
        """Persist SERP results and derive potential backlink candidates (without duplication)."""
        campaign = self.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            return 0
        existing_urls = {r.url for r in self.get_backlink_results(campaign_id, user_email)}
        # Track canonical forms to avoid duplicates like trailing slashes or query params
        existing_canonical: Set[str] = {self._canonical_url(u) for u in existing_urls}
        inserted = 0
        backlink_payload = []
        today = date.today()
        for r in serp_results:
            url = r.get('url')
            if not url:
                continue
            canon = self._canonical_url(url)
            if canon in existing_canonical:
                continue
            # Store SERP ranking
            sr = SerpRanking(
                campaign_id=campaign_id,
                keyword=keyword,
                url=url,
                position=r.get('position'),
                page_title=r.get('page_title'),
                check_date=today
            )
            self.db.add(sr)
            inserted += 1
            # If new URL (not already backlink), enqueue as potential coverage
            if url not in existing_urls:
                backlink_payload.append({
                    'url': url,
                    'coverage_status': 'potential',
                    'source_api': 'serp',
                    'first_seen': today,
                    'domain_rating': None,
                    'confidence_score': None
                })
                existing_canonical.add(canon)
        if inserted:
            self.db.commit()
        if backlink_payload:
            self.add_backlink_results(campaign_id, backlink_payload)
        return inserted
    
    def get_campaign_stats(self, campaign_id: int, user_email: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        campaign = self.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            return {}
        
        backlink_count = self.db.query(BacklinkResult).filter(
            BacklinkResult.campaign_id == campaign_id
        ).count()
        
        verified_count = self.db.query(BacklinkResult).filter(
            and_(
                BacklinkResult.campaign_id == campaign_id,
                BacklinkResult.coverage_status == "verified"
            )
        ).count()
        
        return {
            "total_backlinks": backlink_count,
            "verified_coverage": verified_count,
            "potential_coverage": backlink_count - verified_count,
            "verification_rate": (verified_count / backlink_count * 100) if backlink_count > 0 else 0
        }

    def get_campaign_coverage_detail(self, campaign_id: int, user_email: str) -> Dict[str, Any]:
        """Detailed coverage stats with destination breakdown and average DR."""
        campaign = self.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            return {}
        q = self.db.query(BacklinkResult).filter(BacklinkResult.campaign_id == campaign_id)
        total = q.count()
        verified = q.filter(BacklinkResult.coverage_status == 'verified').count()
        # Average DR
        dr_values = [r.domain_rating for r in q.all() if r.domain_rating is not None]
        avg_dr = sum(dr_values)/len(dr_values) if dr_values else None
        # Destination breakdown
        dest_counts = {}
        for r in q.all():
            dest = r.link_destination or 'unknown'
            dest_counts[dest] = dest_counts.get(dest, 0) + 1
        breakdown = []
        for dest, cnt in dest_counts.items():
            breakdown.append({
                'destination': dest,
                'count': cnt,
                'percentage': (cnt/total*100) if total else 0
            })
        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.campaign_name,
            'client_domain': campaign.client_domain,
            'total_backlinks': total,
            'verified_coverage': verified,
            'potential_coverage': total - verified,
            'verification_rate': (verified/total*100) if total else 0,
            'avg_domain_rating': avg_dr,
            'last_updated': campaign.updated_at.isoformat() if campaign.updated_at else None,
            'last_backlink_fetch_at': campaign.last_backlink_fetch_at.isoformat() if getattr(campaign, 'last_backlink_fetch_at', None) else None,
            'destination_breakdown': breakdown
        }

    def get_aggregate_coverage(self, user_email: str) -> Dict[str, Any]:
        """Aggregate coverage across all campaigns for a user."""
        campaigns = self.get_campaigns_by_user(user_email)
        summaries = []
        total_backlinks = 0
        total_verified = 0
        dr_accum = []
        for c in campaigns:
            detail = self.get_campaign_coverage_detail(c.id, user_email)
            if detail:
                summaries.append(detail)
                total_backlinks += detail['total_backlinks']
                total_verified += detail['verified_coverage']
                if detail.get('avg_domain_rating'):
                    dr_accum.append(detail['avg_domain_rating'])
        total_potential = total_backlinks - total_verified
        overall_rate = (total_verified/total_backlinks*100) if total_backlinks else 0
        avg_dr = sum(dr_accum)/len(dr_accum) if dr_accum else None
        return {
            'total_campaigns': len(campaigns),
            'total_backlinks': total_backlinks,
            'total_verified': total_verified,
            'total_potential': total_potential,
            'overall_verification_rate': overall_rate,
            'average_dr': avg_dr,
            'campaigns': summaries
        }

    # ----------------- Operational / Maintenance Utilities -----------------
    def autopause_expired_campaigns(self, older_than_days: int = 365) -> int:
        """Auto-pause campaigns whose launch_date is older than threshold and currently Live.

        Returns number of campaigns updated.
        """
        cutoff = date.today() - timedelta(days=older_than_days)
        q = self.db.query(Campaign).filter(
            Campaign.launch_date != None,  # noqa: E711
            Campaign.launch_date < cutoff,
            Campaign.monitoring_status == 'Live'
        )
        to_update = q.all()
        updated = 0
        for c in to_update:
            c.monitoring_status = 'Paused'
            updated += 1
        if updated:
            self.db.commit()
        return updated

    # ----------------- Helpers -----------------
    @staticmethod
    def _canonical_url(url: str) -> str:
        """Produce a canonical form for dedupe (strip scheme, query, fragment, trailing slash)."""
        try:
            from urllib.parse import urlparse
            p = urlparse(url)
            path = p.path.rstrip('/')
            return f"{p.netloc.lower()}{path.lower()}"
        except Exception:
            return url.lower().rstrip('/')

def campaign_to_dict(campaign: Campaign) -> Dict[str, Any]:
    """Convert SQLAlchemy Campaign model to dictionary"""
    return {
        "id": campaign.id,
        "user_email": campaign.user_email,
        "client_name": campaign.client_name,
        "campaign_name": campaign.campaign_name,
        "client_domain": campaign.client_domain,
        "campaign_url": campaign.campaign_url,
        "launch_date": campaign.launch_date.isoformat() if campaign.launch_date else None,
        "monitoring_status": campaign.monitoring_status,
        "auto_pause_date": campaign.auto_pause_date.isoformat() if campaign.auto_pause_date else None,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    "last_backlink_fetch_at": campaign.last_backlink_fetch_at.isoformat() if getattr(campaign, 'last_backlink_fetch_at', None) else None,
        "serp_keywords": [k.keyword for k in campaign.keywords if k.keyword_type == "serp"],
        "verification_keywords": [k.keyword for k in campaign.keywords if k.keyword_type == "verification"],
        "blacklist_domains": [b.domain for b in campaign.blacklist_domains]
    }
