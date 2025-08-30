"""
DataForSEO API client for comprehensive SEO data.
"""
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_api import BaseAPIClient, APIResponse
from config.settings import settings


class DataForSEOClient(BaseAPIClient):
    """DataForSEO API client."""
    
    def __init__(self):
        super().__init__(
            base_url="https://api.dataforseo.com/v3",
            timeout=60  # DataForSEO can be slower
        )
        self.username = settings.DATAFORSEO_USERNAME
        self.password = settings.DATAFORSEO_PASSWORD
        self._max_requests_per_minute = 2000  # DataForSEO has high rate limits
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for DataForSEO API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.username and self.password:
            # DataForSEO uses basic auth
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        return headers
    
    async def get_domain_overview(self, domain: str) -> APIResponse:
        """Get comprehensive domain overview."""
        endpoint = "domain_analytics/technologies/domain_technologies/live"
        data = [{
            "target": domain,
            "include_subdomains": True
        }]
        return await self.post(endpoint, data)
    
    async def get_backlinks_overview(self, target: str) -> APIResponse:
        """Get backlinks overview for domain."""
        endpoint = "backlinks/summary/live"
        data = [{
            "target": target,
            "include_subdomains": True
        }]
        return await self.post(endpoint, data)
    
    async def get_backlinks_detailed(
        self,
        target: str,
        limit: int = 100,
        offset: int = 0,
        filters: List[Dict] = None
    ) -> APIResponse:
        """Get detailed backlinks data."""
        endpoint = "backlinks/backlinks/live"
        
        request_data = {
            "target": target,
            "limit": min(limit, 1000),
            "offset": offset,
            "include_subdomains": True,
            "order_by": ["rank,desc"]
        }
        
        if filters:
            request_data["filters"] = filters
        
        data = [request_data]
        return await self.post(endpoint, data)
    
    async def get_referring_domains(
        self,
        target: str,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """Get referring domains analysis."""
        endpoint = "backlinks/referring_domains/live"
        data = [{
            "target": target,
            "limit": min(limit, 1000),
            "offset": offset,
            "include_subdomains": True,
            "order_by": ["backlinks,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_anchors_analysis(self, target: str) -> APIResponse:
        """Get anchor text analysis."""
        endpoint = "backlinks/anchors/live"
        data = [{
            "target": target,
            "limit": 1000,
            "include_subdomains": True,
            "order_by": ["backlinks,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_competitors_backlinks(
        self,
        target: str,
        competitors: List[str],
        intersection_mode: str = "all"
    ) -> APIResponse:
        """Get competitor backlinks analysis."""
        endpoint = "backlinks/competitors/live"
        
        targets = [target] + competitors
        
        data = [{
            "targets": targets,
            "limit": 1000,
            "intersection_mode": intersection_mode,  # "all", "any", "target_only"
            "order_by": ["intersections,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_bulk_backlinks_overview(self, targets: List[str]) -> APIResponse:
        """Get backlinks overview for multiple targets."""
        endpoint = "backlinks/bulk_summary/live"
        data = []
        
        for target in targets:
            data.append({
                "target": target,
                "include_subdomains": True
            })
        
        return await self.post(endpoint, data)
    
    async def get_page_intersection(
        self,
        targets: List[str],
        limit: int = 100
    ) -> APIResponse:
        """Find pages that link to multiple targets."""
        endpoint = "backlinks/page_intersection/live"
        data = [{
            "targets": targets,
            "limit": min(limit, 1000),
            "order_by": ["intersections,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_domain_intersection(
        self,
        targets: List[str],
        limit: int = 100
    ) -> APIResponse:
        """Find domains that link to multiple targets."""
        endpoint = "backlinks/domain_intersection/live"
        data = [{
            "targets": targets,
            "limit": min(limit, 1000),
            "order_by": ["intersections,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_historical_backlinks(
        self,
        target: str,
        date_from: str,
        date_to: str = None
    ) -> APIResponse:
        """Get historical backlinks data."""
        endpoint = "backlinks/history/live"
        
        request_data = {
            "target": target,
            "date_from": date_from,
            "include_subdomains": True
        }
        
        if date_to:
            request_data["date_to"] = date_to
        
        data = [request_data]
        return await self.post(endpoint, data)
    
    async def get_toxic_backlinks(self, target: str) -> APIResponse:
        """Identify potentially toxic backlinks."""
        endpoint = "backlinks/backlinks/live"
        
        # Filter for potentially toxic indicators
        toxic_filters = [
            ["domain_rank", "<", 10],  # Low domain authority
            ["spam_score", ">", 50],   # High spam score
            ["broken_redirect", "=", True]  # Broken redirects
        ]
        
        data = [{
            "target": target,
            "limit": 1000,
            "include_subdomains": True,
            "filters": toxic_filters,
            "order_by": ["first_seen,desc"]
        }]
        return await self.post(endpoint, data)
    
    async def get_new_lost_backlinks(
        self,
        target: str,
        date_from: str,
        comparison_date: str
    ) -> APIResponse:
        """Get new and lost backlinks between two time periods."""
        endpoint = "backlinks/timeseries_new_lost_summary/live"
        data = [{
            "target": target,
            "date_from": date_from,
            "date_to": comparison_date,
            "include_subdomains": True
        }]
        return await self.post(endpoint, data)
    
    async def analyze_link_quality(self, target: str) -> APIResponse:
        """Comprehensive link quality analysis."""
        # This combines multiple endpoints for comprehensive analysis
        try:
            # Get basic backlinks data
            backlinks_response = await self.get_backlinks_detailed(target, limit=1000)
            
            if not backlinks_response.success:
                return backlinks_response
            
            # Additional analysis could be added here
            # For now, return the comprehensive backlinks data
            return backlinks_response
            
        except Exception as e:
            self.logger.error(f"Link quality analysis failed for {target}: {str(e)}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                source=self.__class__.__name__
            )
    
    async def get_serp_features(
        self,
        keyword: str,
        location_code: int = 2840,  # USA
        language_code: str = "en"
    ) -> APIResponse:
        """Get SERP features for keyword analysis."""
        endpoint = "serp/google/organic/live/advanced"
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": "desktop",
            "os": "windows"
        }]
        return await self.post(endpoint, data)
