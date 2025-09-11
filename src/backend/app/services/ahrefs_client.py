"""
Ahrefs API client for backlink and domain analysis.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.utils.datetime_utils import utc_now

from .base_api import BaseAPIClient, APIResponse
from config.settings import settings


class AhrefsClient(BaseAPIClient):
    """Ahrefs API client."""
    
    def __init__(self):
        super().__init__(
            base_url="https://apiv2.ahrefs.com",
            api_key=settings.AHREFS_API_KEY,
            timeout=30
        )
        self._max_requests_per_minute = 60  # Ahrefs rate limit
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Ahrefs API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def get_domain_overview(self, domain: str) -> APIResponse:
        """Get domain overview including DR, traffic, and backlinks count."""
        endpoint = f"domain-rating"
        params = {
            "target": domain,
            "mode": "domain"
        }
        return await self.get(endpoint, params)
    
    async def get_backlinks(
        self,
        target: str,
        mode: str = "domain",
        limit: int = 100,
        offset: int = 0,
        order_by: str = "domain_rating_source:desc"
    ) -> APIResponse:
        """Get backlinks for a target domain or URL."""
        endpoint = "backlinks"
        params = {
            "target": target,
            "mode": mode,
            "limit": min(limit, 1000),  # Ahrefs max limit
            "offset": offset,
            "order_by": order_by,
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def get_referring_domains(
        self,
        target: str,
        mode: str = "domain",
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """Get referring domains for a target."""
        endpoint = "refdomains"
        params = {
            "target": target,
            "mode": mode,
            "limit": min(limit, 1000),
            "offset": offset,
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def get_top_pages(
        self,
        target: str,
        limit: int = 50,
        offset: int = 0
    ) -> APIResponse:
        """Get top pages by organic traffic."""
        endpoint = "pages"
        params = {
            "target": target,
            "mode": "domain",
            "limit": min(limit, 1000),
            "offset": offset,
            "order_by": "organic_traffic:desc",
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def get_organic_keywords(
        self,
        target: str,
        limit: int = 100,
        offset: int = 0,
        volume_from: int = None,
        volume_to: int = None
    ) -> APIResponse:
        """Get organic keywords for a domain."""
        endpoint = "organic-keywords"
        params = {
            "target": target,
            "mode": "domain",
            "limit": min(limit, 1000),
            "offset": offset,
            "order_by": "volume:desc",
            "output": "json"
        }
        
        if volume_from:
            params["volume_from"] = volume_from
        if volume_to:
            params["volume_to"] = volume_to
            
        return await self.get(endpoint, params)
    
    async def get_broken_backlinks(self, target: str) -> APIResponse:
        """Get broken backlinks for a target."""
        endpoint = "backlinks-broken"
        params = {
            "target": target,
            "mode": "domain",
            "limit": 1000,
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def get_new_backlinks(
        self,
        target: str,
        days: int = 7
    ) -> APIResponse:
        """Get new backlinks from the last N days."""
        endpoint = "backlinks-new"
        params = {
            "target": target,
            "mode": "domain",
            "limit": 1000,
            "date_from": (datetime.now().date() - timedelta(days=days)).isoformat(),
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def get_lost_backlinks(
        self,
        target: str,
        days: int = 7
    ) -> APIResponse:
        """Get lost backlinks from the last N days."""
        endpoint = "backlinks-lost"
        params = {
            "target": target,
            "mode": "domain",
            "limit": 1000,
            "date_from": (datetime.now().date() - timedelta(days=days)).isoformat(),
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def analyze_competitor_backlinks(
        self,
        target_domain: str,
        competitor_domain: str,
        common_only: bool = False
    ) -> APIResponse:
        """Analyze backlinks between target and competitor."""
        # This would typically require multiple API calls and processing
        # For now, return backlinks from competitor that don't link to target
        
        if common_only:
            # Get backlinks that link to both domains
            endpoint = "backlinks-comparison"
            params = {
                "targets": f"{target_domain},{competitor_domain}",
                "mode": "domain",
                "intersection": "true",
                "limit": 1000,
                "output": "json"
            }
        else:
            # Get competitor backlinks
            endpoint = "backlinks"
            params = {
                "target": competitor_domain,
                "mode": "domain",
                "limit": 1000,
                "output": "json"
            }
        
        return await self.get(endpoint, params)
    
    async def get_anchor_distribution(self, target: str) -> APIResponse:
        """Get anchor text distribution for backlinks."""
        endpoint = "anchors"
        params = {
            "target": target,
            "mode": "domain",
            "limit": 1000,
            "order_by": "backlinks:desc",
            "output": "json"
        }
        return await self.get(endpoint, params)
    
    async def batch_domain_metrics(self, domains: List[str]) -> Dict[str, APIResponse]:
        """Get domain metrics for multiple domains."""
        results = {}
        
        for domain in domains:
            try:
                response = await self.get_domain_overview(domain)
                results[domain] = response
            except Exception as e:
                self.logger.error(f"Failed to get metrics for {domain}: {str(e)}")
                results[domain] = APIResponse(
                    success=False,
                    data=None,
                    error=str(e),
                    response_time_ms=0,
                    timestamp=utc_now(),
                    source=self.__class__.__name__
                )
        
        return results
