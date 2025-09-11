"""
Service aggregator for combining Ahrefs and DataForSEO data.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from app.utils.datetime_utils import utc_now, iso_utc_now
import logging
import sys
import os

# Add the backend root to Python path to import from services
backend_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, backend_root)

from .external.ahrefs_client import AhrefsClient
from .external.dataforseo_client import DataForSeoClient
from .base_api import APIResponse, MockAPIClient
from app.models.backlink import BacklinkProfile, ReferringDomain, Backlink
from app.models.analysis import QualityScore, CompetitorInsight, LinkOpportunity, RiskAlert
from config.settings import settings

# Import enhanced mock data service
try:
    from services.mock_data_service import mock_data_service
except ImportError:
    # Fallback if import fails
    mock_data_service = None


class LinkAnalysisService:
    """Aggregated service for comprehensive link analysis."""
    
    def __init__(self, use_mock: bool = None):
        self.logger = logging.getLogger(__name__)
        
        # Auto-detect if we should use real APIs based on credentials
        has_ahrefs_key = settings.AHREFS_API_KEY is not None and settings.AHREFS_API_KEY != ""
        has_dataforseo_creds = (settings.DATAFORSEO_USERNAME is not None and 
                               settings.DATAFORSEO_PASSWORD is not None and
                               settings.DATAFORSEO_USERNAME != "" and 
                               settings.DATAFORSEO_PASSWORD != "")
        
        # Override with explicit parameter if provided
        if use_mock is None:
            use_mock = not (has_ahrefs_key or has_dataforseo_creds)
        
        self.use_real_apis = not use_mock
        
        if use_mock:
            self.logger.info("Using mock API clients for development")
            self.ahrefs = MockAPIClient("https://mock-ahrefs.com", "mock-key")
            self.dataforseo = MockAPIClient("https://mock-dataforseo.com", "mock-key")
        else:
            self.logger.info("Using real API clients with live credentials")
            self.ahrefs = AhrefsClient() if has_ahrefs_key else None
            self.dataforseo = DataForSeoClient() if has_dataforseo_creds else None
            
            if not self.ahrefs and not self.dataforseo:
                self.logger.warning("No API credentials available, falling back to mock data")
                self.ahrefs = MockAPIClient("https://mock-ahrefs.com", "mock-key")
                self.dataforseo = MockAPIClient("https://mock-dataforseo.com", "mock-key")
                self.use_real_apis = False
    
    async def get_comprehensive_analysis(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive backlink analysis from both APIs."""
        try:
            # Run both API calls concurrently
            ahrefs_task = self.ahrefs.get_domain_overview(domain)
            dataforseo_task = self.dataforseo.get_backlinks_overview(domain)
            
            ahrefs_result, dataforseo_result = await asyncio.gather(
                ahrefs_task, dataforseo_task, return_exceptions=True
            )
            
            # Process results
            analysis = {
                "domain": domain,
                "timestamp": iso_utc_now(),
                "sources": {},
                "aggregated_metrics": {},
                "recommendations": []
            }
            
            # Process Ahrefs data
            if isinstance(ahrefs_result, APIResponse) and ahrefs_result.success:
                analysis["sources"]["ahrefs"] = {
                    "status": "success",
                    "data": ahrefs_result.data,
                    "response_time_ms": ahrefs_result.response_time_ms
                }
            else:
                analysis["sources"]["ahrefs"] = {
                    "status": "error",
                    "error": str(ahrefs_result) if isinstance(ahrefs_result, Exception) else ahrefs_result.error
                }
            
            # Process DataForSEO data
            if isinstance(dataforseo_result, APIResponse) and dataforseo_result.success:
                analysis["sources"]["dataforseo"] = {
                    "status": "success",
                    "data": dataforseo_result.data,
                    "response_time_ms": dataforseo_result.response_time_ms
                }
            else:
                analysis["sources"]["dataforseo"] = {
                    "status": "error",
                    "error": str(dataforseo_result) if isinstance(dataforseo_result, Exception) else dataforseo_result.error
                }
            
            # Aggregate metrics from both sources
            analysis["aggregated_metrics"] = self._aggregate_metrics(
                ahrefs_result if isinstance(ahrefs_result, APIResponse) else None,
                dataforseo_result if isinstance(dataforseo_result, APIResponse) else None
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed for {domain}: {str(e)}")
            return {
                "domain": domain,
                "timestamp": iso_utc_now(),
                "error": str(e),
                "sources": {},
                "aggregated_metrics": {},
                "recommendations": []
            }
    
    async def get_backlink_profile(self, domain: str) -> BacklinkProfile:
        """Get detailed backlink profile using enhanced mock data."""
        try:
            # First try to get enhanced mock data
            if mock_data_service:
                mock_data = mock_data_service.get_backlink_data(domain)
                if mock_data:
                    return self._convert_mock_to_profile(mock_data)
                else:
                    # Generate fallback data for unknown domains
                    fallback_data = mock_data_service.generate_fallback_data(f"https://{domain}")
                    return self._convert_mock_to_profile(fallback_data)
            
            # Fallback to original API logic if mock service unavailable
            # Get data from both sources
            ahrefs_backlinks = await self.ahrefs.get_backlinks(domain, limit=500)
            ahrefs_domains = await self.ahrefs.get_referring_domains(domain, limit=200)
            dataforseo_backlinks = await self.dataforseo.get_backlinks_detailed(domain, limit=500)
            
            # Process and aggregate data
            backlinks = []
            referring_domains = []
            
            # Process Ahrefs backlinks
            if ahrefs_backlinks.success and ahrefs_backlinks.data:
                backlinks.extend(self._process_ahrefs_backlinks(ahrefs_backlinks.data))
            
            # Process DataForSEO backlinks
            if dataforseo_backlinks.success and dataforseo_backlinks.data:
                backlinks.extend(self._process_dataforseo_backlinks(dataforseo_backlinks.data))
            
            # Process referring domains
            if ahrefs_domains.success and ahrefs_domains.data:
                referring_domains.extend(self._process_ahrefs_domains(ahrefs_domains.data))
            
            # Calculate metrics
            total_backlinks = len(backlinks)
            total_domains = len(referring_domains)
            dofollow_count = sum(1 for bl in backlinks if bl.link_type == "dofollow")
            
            return BacklinkProfile(
                target_url=f"https://{domain}",
                target_domain=domain,
                total_backlinks=total_backlinks,
                total_referring_domains=total_domains,
                dofollow_backlinks=dofollow_count,
                nofollow_backlinks=total_backlinks - dofollow_count,
                average_domain_rating=sum(bl.domain_rating for bl in backlinks if bl.domain_rating) / len(backlinks) if backlinks else None,
                backlinks=backlinks[:100],  # Limit for response size
                referring_domains=referring_domains[:50],
                last_analyzed=utc_now()
            )
            
        except Exception as e:
            self.logger.error(f"Backlink profile analysis failed for {domain}: {str(e)}")
            return BacklinkProfile(
                target_url=f"https://{domain}",
                target_domain=domain,
                total_backlinks=0,
                total_referring_domains=0,
                dofollow_backlinks=0,
                nofollow_backlinks=0,
                backlinks=[],
                referring_domains=[],
                last_analyzed=utc_now()
            )
    
    async def analyze_competitor_gaps(
        self,
        target_domain: str,
        competitor_domains: List[str]
    ) -> List[LinkOpportunity]:
        """Analyze competitor backlink gaps."""
        opportunities = []
        
        try:
            # Get competitor intersection data
            for competitor in competitor_domains:
                # Get backlinks that competitor has but target doesn't
                competitor_backlinks = await self.ahrefs.analyze_competitor_backlinks(
                    target_domain, competitor, common_only=False
                )
                
                if competitor_backlinks.success and competitor_backlinks.data:
                    # Process gaps (simplified logic)
                    gaps = self._identify_link_gaps(competitor_backlinks.data, competitor)
                    opportunities.extend(gaps[:10])  # Limit opportunities per competitor
            
            # Sort by priority score
            opportunities.sort(key=lambda x: x.priority_score, reverse=True)
            return opportunities[:50]  # Return top 50 opportunities
            
        except Exception as e:
            self.logger.error(f"Competitor gap analysis failed: {str(e)}")
            return []
    
    async def assess_link_risks(self, domain: str) -> List[RiskAlert]:
        """Assess potential link risks."""
        risks = []
        
        try:
            # Get toxic backlinks from DataForSEO
            toxic_links = await self.dataforseo.get_toxic_backlinks(domain)
            
            if toxic_links.success and toxic_links.data:
                risks.extend(self._process_toxic_links(toxic_links.data))
            
            # Get broken backlinks from Ahrefs
            broken_links = await self.ahrefs.get_broken_backlinks(domain)
            
            if broken_links.success and broken_links.data:
                risks.extend(self._process_broken_links(broken_links.data))
            
            # Sort by severity
            risks.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}[x.severity], reverse=True)
            return risks[:100]  # Return top 100 risks
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed for {domain}: {str(e)}")
            return []
    
    def _aggregate_metrics(
        self,
        ahrefs_response: Optional[APIResponse],
        dataforseo_response: Optional[APIResponse]
    ) -> Dict[str, Any]:
        """Aggregate metrics from both API sources."""
        metrics = {
            "domain_authority": None,
            "backlinks_count": None,
            "referring_domains": None,
            "organic_traffic": None,
            "data_freshness": iso_utc_now(),
            "confidence_score": 0
        }
        
        confidence_factors = []
        
        # Process Ahrefs metrics
        if ahrefs_response and ahrefs_response.success:
            ahrefs_data = ahrefs_response.data
            if isinstance(ahrefs_data, dict):
                metrics["domain_authority"] = ahrefs_data.get("domain_rating")
                metrics["backlinks_count"] = ahrefs_data.get("backlinks_count")
                metrics["referring_domains"] = ahrefs_data.get("referring_domains")
                metrics["organic_traffic"] = ahrefs_data.get("organic_traffic")
                confidence_factors.append(0.6)  # Ahrefs weight
        
        # Process DataForSEO metrics (could override or average with Ahrefs)
        if dataforseo_response and dataforseo_response.success:
            confidence_factors.append(0.4)  # DataForSEO weight
        
        # Calculate confidence score
        metrics["confidence_score"] = sum(confidence_factors)
        
        return metrics
    
    def _process_ahrefs_backlinks(self, data: Dict[str, Any]) -> List[Backlink]:
        """Process Ahrefs backlinks data."""
        backlinks = []
        
        for item in data.get("backlinks", []):
            backlink = Backlink(
                url_from=item.get("url_from", ""),
                url_to=item.get("url_to", ""),
                anchor_text=item.get("anchor", ""),
                domain_rating=item.get("domain_rating", 0),
                url_rating=item.get("url_rating", 0),
                first_seen=datetime.fromisoformat(item.get("first_seen", utc_now().isoformat())),
                last_seen=datetime.fromisoformat(item.get("last_seen", utc_now().isoformat())),
                link_type=item.get("link_type", "unknown"),
                is_redirect=item.get("is_redirect", False),
                is_canonical=item.get("is_canonical", False),
                is_alternate=item.get("is_alternate", False)
            )
            backlinks.append(backlink)
        
        return backlinks
    
    def _process_dataforseo_backlinks(self, data: Dict[str, Any]) -> List[Backlink]:
        """Process DataForSEO backlinks data."""
        backlinks = []
        
        # DataForSEO has nested structure
        for task in data.get("tasks", []):
            for result in task.get("result", []):
                for item in result.get("items", []):
                    backlink = Backlink(
                        url_from=item.get("source_url", ""),
                        url_to=item.get("target_url", ""),
                        anchor_text=item.get("anchor", ""),
                        domain_rating=item.get("domain_rank", 0),
                        url_rating=item.get("page_rank", 0),
                        first_seen=datetime.fromisoformat(item.get("first_seen", utc_now().isoformat())),
                        last_seen=datetime.fromisoformat(item.get("last_seen", utc_now().isoformat())),
                        link_type="dofollow" if not item.get("nofollow") else "nofollow",
                        is_redirect=item.get("redirect", False),
                        is_canonical=False,  # Would need additional processing
                        is_alternate=False
                    )
                    backlinks.append(backlink)
        
        return backlinks
    
    def _process_ahrefs_domains(self, data: Dict[str, Any]) -> List[ReferringDomain]:
        """Process Ahrefs referring domains data."""
        domains = []
        
        for item in data.get("refdomains", []):
            domain = ReferringDomain(
                domain=item.get("domain", ""),
                domain_rating=item.get("domain_rating", 0),
                backlinks_count=item.get("backlinks", 0),
                first_seen=datetime.fromisoformat(item.get("first_seen", utc_now().isoformat())),
                last_seen=datetime.fromisoformat(item.get("last_seen", utc_now().isoformat())),
                link_type_distribution={
                    "dofollow": item.get("dofollow", 0),
                    "nofollow": item.get("nofollow", 0)
                }
            )
            domains.append(domain)
        
        return domains
    
    def _identify_link_gaps(self, data: Dict[str, Any], competitor: str) -> List[LinkOpportunity]:
        """Identify link opportunities from competitor analysis."""
        opportunities = []
        
        # Simplified gap analysis
        for item in data.get("backlinks", [])[:20]:  # Limit processing
            opportunity = LinkOpportunity(
                target_url=item.get("url_from", ""),
                source_domain=item.get("domain", ""),
                competitor_domain=competitor,
                anchor_suggestion=item.get("anchor", ""),
                priority_score=min(item.get("domain_rating", 0) / 10, 10),  # Normalize to 1-10
                opportunity_type="competitor_gap",
                contact_info=None,  # Would need additional lookup
                estimated_effort="medium"
            )
            opportunities.append(opportunity)
        
        return opportunities
    
    def _process_toxic_links(self, data: Dict[str, Any]) -> List[RiskAlert]:
        """Process toxic links into risk alerts."""
        risks = []
        
        # Process DataForSEO toxic links
        for task in data.get("tasks", []):
            for result in task.get("result", []):
                for item in result.get("items", []):
                    risk = RiskAlert(
                        risk_type="toxic_link",
                        severity="high",
                        description=f"Potentially toxic backlink from {item.get('source_url', 'unknown')}",
                        affected_urls=[item.get("target_url", "")],
                        recommendation="Consider disavowing this link",
                        detected_date=utc_now()
                    )
                    risks.append(risk)
        
        return risks
    
    def _process_broken_links(self, data: Dict[str, Any]) -> List[RiskAlert]:
        """Process broken links into risk alerts."""
        risks = []
        
        for item in data.get("backlinks", []):
            risk = RiskAlert(
                risk_type="broken_link",
                severity="medium",
                description=f"Broken backlink from {item.get('url_from', 'unknown')}",
                affected_urls=[item.get("url_to", "")],
                recommendation="Fix the target URL or contact the linking site",
                detected_date=utc_now()
            )
            risks.append(risk)
        
        return risks
    
    def _convert_mock_to_profile(self, mock_data: Dict[str, Any]) -> BacklinkProfile:
        """Convert enhanced mock data to BacklinkProfile model."""
        try:
            # Convert top referring domains to ReferringDomain objects
            referring_domains = []
            for domain_data in mock_data.get("top_referring_domains", []):
                do_count = domain_data.get("backlinks", 0) if domain_data.get("link_type") == "dofollow" else 0
                no_count = domain_data.get("backlinks", 0) if domain_data.get("link_type") == "nofollow" else 0
                referring_domain = ReferringDomain(
                    domain=domain_data.get("domain", ""),
                    domain_rating=domain_data.get("domain_rating", 0),
                    backlinks_count=domain_data.get("backlinks", 0),
                    first_seen=datetime.fromisoformat(domain_data.get("first_seen", utc_now().isoformat())),
                    last_seen=datetime.fromisoformat(domain_data.get("last_seen", utc_now().isoformat())),
                    dofollow_links=do_count,
                    nofollow_links=no_count,
                )
                referring_domains.append(referring_domain)
            
            # Generate sample backlinks from referring domains data
            backlinks = []
            for domain_data in mock_data.get("top_referring_domains", [])[:20]:  # Create backlinks from top domains
                for anchor in domain_data.get("anchor_texts", [domain_data.get("domain", "")])[:3]:  # Max 3 per domain
                    backlink = Backlink(
                        url_from=f"https://{domain_data.get('domain', '')}/page{len(backlinks)}",
                        url_to=mock_data.get("target_url", ""),
                        anchor_text=anchor,
                        domain_rating=domain_data.get("domain_rating", 0),
                        url_rating=domain_data.get("url_rating", domain_data.get("domain_rating", 0) - 5),
                        first_seen=datetime.fromisoformat(domain_data.get("first_seen", utc_now().isoformat())),
                        last_seen=datetime.fromisoformat(domain_data.get("last_seen", utc_now().isoformat())),
                        link_type=domain_data.get("link_type", "dofollow"),
                        data_source="mock",
                        is_redirect=False,
                        is_canonical=False,
                        is_alternate=False
                    )
                    backlinks.append(backlink)
            
            # Parse last analyzed date
            last_analyzed = datetime.fromisoformat(mock_data.get("last_analyzed", utc_now().isoformat()).replace('Z', '+00:00'))
            
            return BacklinkProfile(
                target_url=mock_data.get("target_url", ""),
                target_domain=mock_data.get("target_domain", ""),
                total_backlinks=mock_data.get("total_backlinks", 0),
                total_referring_domains=mock_data.get("referring_domains", 0),
                dofollow_backlinks=mock_data.get("dofollow_backlinks", 0),
                nofollow_backlinks=mock_data.get("nofollow_backlinks", 0),
                average_domain_rating=mock_data.get("average_domain_rating"),
                backlinks=backlinks,
                referring_domains=referring_domains,
                last_analyzed=last_analyzed
            )
            
        except Exception as e:
            self.logger.error(f"Error converting mock data to profile: {str(e)}")
            # Return minimal profile on error
            return BacklinkProfile(
                target_url=mock_data.get("target_url", ""),
                target_domain=mock_data.get("target_domain", ""),
                total_backlinks=0,
                total_referring_domains=0,
                dofollow_backlinks=0,
                nofollow_backlinks=0,
                backlinks=[],
                referring_domains=[],
                last_analyzed=utc_now()
            )
