"""
Base API client for external service integrations.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

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
        
        start_time = datetime.utcnow()
        
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                end_time = datetime.utcnow()
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
                timestamp=datetime.utcnow(),
                source=self.__class__.__name__
            )
        except Exception as e:
            self.logger.error(f"Request failed for {method} {url}: {str(e)}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                source=self.__class__.__name__
            )
    
    async def _apply_rate_limit(self):
        """Apply rate limiting before making requests."""
        now = datetime.utcnow()
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
        timestamp = datetime.utcnow()
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
            timestamp=datetime.utcnow(),
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
