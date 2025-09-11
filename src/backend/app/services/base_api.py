"""
Base API client for external service integrations.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from app.utils.datetime_utils import utc_now

import httpx
from httpx import AsyncClient, Response
from pydantic import BaseModel

from config.settings import settings


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    requests_per_minute: int
    requests_remaining: int
    reset_time: datetime
    burst_limit: int


class APIResponse(BaseModel):
    """Standardized API response."""
    success: bool
    data: Any
    error: Optional[str] = None
    rate_limit: Optional[RateLimitInfo] = None
    response_time_ms: int
    timestamp: datetime
    source: str


class BaseAPIClient(ABC):
    """Base class for external API clients."""
    
    def __init__(self, base_url: str, api_key: str = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._max_requests_per_minute = 60
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> APIResponse:
        """Make HTTP request with rate limiting and error handling."""
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        start_time = utc_now()
        
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                end_time = utc_now()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Log request
                self.logger.info(
                    f"{method} {url} - {response.status_code} ({response_time_ms}ms)"
                )
                
                # Handle response
                return await self._handle_response(response, response_time_ms)
                
        except httpx.TimeoutException:
            self.logger.error(f"Request timeout for {method} {url}")
            return APIResponse(
                success=False,
                data=None,
                error="Request timeout",
                response_time_ms=self.timeout * 1000,
                timestamp=utc_now(),
                source=self.__class__.__name__
            )
        except Exception as e:
            self.logger.error(f"Request failed for {method} {url}: {str(e)}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time_ms=0,
                timestamp=utc_now(),
                source=self.__class__.__name__
            )
    
    async def _apply_rate_limit(self):
        """Apply rate limiting before making requests."""
        now = utc_now()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old requests
        self._request_times = [t for t in self._request_times if t > cutoff]
        
        # Check if we need to wait
        if len(self._request_times) >= self._max_requests_per_minute:
            wait_time = 60 - (now - self._request_times[0]).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self._request_times.append(now)
    
    async def _handle_response(self, response: Response, response_time_ms: int) -> APIResponse:
        """Handle HTTP response and convert to APIResponse."""
        timestamp = utc_now()
        source = self.__class__.__name__
        
        try:
            if response.status_code == 200:
                data = response.json()
                return APIResponse(
                    success=True,
                    data=data,
                    response_time_ms=response_time_ms,
                    timestamp=timestamp,
                    source=source
                )
            elif response.status_code == 429:
                # Rate limited
                return APIResponse(
                    success=False,
                    data=None,
                    error="Rate limit exceeded",
                    response_time_ms=response_time_ms,
                    timestamp=timestamp,
                    source=source
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return APIResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    response_time_ms=response_time_ms,
                    timestamp=timestamp,
                    source=source
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                data=None,
                error=f"Response parsing error: {str(e)}",
                response_time_ms=response_time_ms,
                timestamp=timestamp,
                source=source
            )
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        pass
    
    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> APIResponse:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> APIResponse:
        """Make POST request."""
        return await self._make_request("POST", endpoint, data=data)


class MockAPIClient(BaseAPIClient):
    """Mock API client for testing and development."""
    
    def _get_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Override to return mock data."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Return mock data based on endpoint
        mock_data = self._get_mock_data(endpoint)
        
        return APIResponse(
            success=True,
            data=mock_data,
            response_time_ms=100,
            timestamp=utc_now(),
            source="MockAPI"
        )
    
    def _get_mock_data(self, endpoint: str) -> Dict[str, Any]:
        """Get mock data based on endpoint."""
        if "backlinks" in endpoint:
            return {
                "total": 1250,
                "backlinks": [
                    {
                        "url_from": "https://example.com/blog/post1",
                        "url_to": "https://target.com/page",
                        "anchor": "great resource",
                        "domain_rating": 65,
                        "first_seen": "2024-01-15",
                        "link_type": "dofollow"
                    }
                ]
            }
        elif "domain" in endpoint:
            return {
                "domain_rating": 72,
                "organic_traffic": 45000,
                "backlinks_count": 156789,
                "referring_domains": 8934
            }
        else:
            return {"message": "Mock response", "endpoint": endpoint}

    # --- Convenience mock methods used by analysis service ---
    async def get_backlinks(self, domain: str, limit: int = 500) -> APIResponse:
        """Return a deterministic set of mock backlinks for a domain (Ahrefs-like shape)."""
        items: List[Dict[str, Any]] = []
        now = utc_now()
        base_domain = domain.replace("https://", "").replace("http://", "")
        for i in range(min(limit, 25)):
            items.append({
                "url_from": f"https://ref{i}.{base_domain}/article/{i}",
                "url_to": f"https://{base_domain}/page/{i%5}",
                "anchor": f"reference {i}",
                "domain_rating": 40 + (i % 60),
                "url_rating": 30 + (i % 50),
                "first_seen": (now.replace(microsecond=0)).isoformat(),
                "last_seen": (now.replace(microsecond=0)).isoformat(),
                "link_type": "dofollow" if i % 4 != 0 else "nofollow",
                "is_redirect": False,
                "is_canonical": False,
                "is_alternate": False,
            })
        data = {"backlinks": items}
        return APIResponse(
            success=True,
            data=data,
            response_time_ms=50,
            timestamp=utc_now(),
            source=self.__class__.__name__,
        )

    async def get_referring_domains(self, domain: str, limit: int = 200) -> APIResponse:
        """Return mock referring domains (Ahrefs-like shape)."""
        items: List[Dict[str, Any]] = []
        now = utc_now()
        for i in range(min(limit, 15)):
            items.append({
                "domain": f"refdomain{i}.com",
                "domain_rating": 35 + (i * 3),
                "backlinks": 1 + (i % 7),
                "first_seen": now.date().isoformat(),
                "last_seen": now.date().isoformat(),
                "dofollow": 1 + (i % 5),
                "nofollow": i % 3,
            })
        data = {"refdomains": items}
        return APIResponse(
            success=True,
            data=data,
            response_time_ms=30,
            timestamp=utc_now(),
            source=self.__class__.__name__,
        )

    async def get_backlinks_detailed(self, domain: str, limit: int = 500) -> APIResponse:
        """Return DataForSEO-shaped mock backlinks structure."""
        base_domain = domain.replace("https://", "").replace("http://", "")
        items: List[Dict[str, Any]] = []
        now = utc_now()
        for i in range(min(limit, 25)):
            items.append({
                "source_url": f"https://source{i}.example.com/path/{i}",
                "target_url": f"https://{base_domain}/target/{i%7}",
                "anchor": f"anchor {i}",
                "domain_rank": 38 + (i % 55),
                "page_rank": 20 + (i % 40),
                "first_seen": now.date().isoformat(),
                "last_seen": now.date().isoformat(),
                "nofollow": (i % 5 == 0),
                "redirect": False,
            })
        data = {"tasks": [{"result": [{"items": items}]}]}
        return APIResponse(
            success=True,
            data=data,
            response_time_ms=70,
            timestamp=utc_now(),
            source=self.__class__.__name__,
        )

    async def get_domain_overview(self, domain: str) -> APIResponse:
        """Return a mock domain overview."""
        data = {
            "domain_rating": 70,
            "organic_traffic": 50000,
            "backlinks_count": 15000,
            "referring_domains": 700,
        }
        return APIResponse(
            success=True,
            data=data,
            response_time_ms=20,
            timestamp=utc_now(),
            source=self.__class__.__name__,
        )
