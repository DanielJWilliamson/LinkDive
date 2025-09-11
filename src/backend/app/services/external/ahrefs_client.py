"""Ahrefs API client (skeleton) with graceful fallback to mock data if API key absent."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote
import httpx
from config.settings import settings
from app.core.rate_limiter import ahrefs_limiter
import logging
from app.core.metrics import metrics
from config.settings import settings as _settings
from app.core.runtime_flags import runtime_flags

@dataclass
class BacklinkRecord:
    url_from: str
    url_to: str
    title: Optional[str]
    first_seen: Optional[str]
    domain_rating: Optional[int]
    source_api: str = "ahrefs"

class AhrefsClient:
    BASE_PATH = "/site-explorer/all-backlinks"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ahrefs_api_key or settings.AHREFS_API_KEY
        self.base_url = settings.ahrefs_base_url.rstrip('/')

    async def fetch_backlinks(self, target: str, mode: str = "prefix", limit: int = 50) -> List[BacklinkRecord]:
        # Force mock when runtime flag is enabled
        if runtime_flags.is_mock_mode():
            metrics.inc("ahrefs_calls_mock")
            return [
                BacklinkRecord(url_from="https://example.com/article-1", url_to=target, title="Example Article 1", first_seen="2025-09-01", domain_rating=42),
                BacklinkRecord(url_from="https://example.com/article-2", url_to=target, title="Example Article 2", first_seen="2025-09-02", domain_rating=13),
            ]
        if not ahrefs_limiter.allow():
            metrics.inc("ahrefs_rate_limit_drops")
            logging.getLogger(__name__).warning("Ahrefs rate limit exceeded; returning empty list this cycle")
            return []
        if not self.api_key:
            # Return deterministic mock
            metrics.inc("ahrefs_calls_mock")
            return [
                BacklinkRecord(url_from="https://example.com/article-1", url_to=target, title="Example Article 1", first_seen="2025-09-01", domain_rating=42),
                BacklinkRecord(url_from="https://example.com/article-2", url_to=target, title="Example Article 2", first_seen="2025-09-02", domain_rating=13),
            ]
        # Support Ahrefs v2 (apiv2.ahrefs.com) and v3 (api.ahrefs.com/v3)
        metrics.inc("ahrefs_calls_real")
        async with httpx.AsyncClient(timeout=30) as client:
            if "apiv2.ahrefs.com" in self.base_url:
                # v2: GET https://apiv2.ahrefs.com?from=backlinks&target=...&mode=prefix&limit=...&output=json&token=...
                # v2 expects double-encoded target for exact/prefix
                target_encoded = quote(quote(target, safe=""), safe="")
                params = {
                    "from": "backlinks",
                    "target": target_encoded,
                    "mode": mode,
                    "limit": str(limit),
                    "output": "json",
                    "token": self.api_key,
                }
                try:
                    resp = await client.get(self.base_url, params=params)
                    resp.raise_for_status()
                    data = resp.json() or {}
                except Exception as e:
                    msg = f"HTTP error: {getattr(e, 'response', None).status_code if hasattr(e, 'response') and getattr(e, 'response') is not None else ''}"
                    logging.getLogger(__name__).warning(f"Ahrefs v2 request failed; {e}")
                    runtime_flags.set_provider_error("ahrefs", msg or str(e))
                    metrics.inc("ahrefs_calls_mock")
                    return [
                        BacklinkRecord(url_from="https://example.com/article-1", url_to=target, title="Example Article 1", first_seen="2025-09-01", domain_rating=42),
                        BacklinkRecord(url_from="https://example.com/article-2", url_to=target, title="Example Article 2", first_seen="2025-09-02", domain_rating=13),
                    ]
                # Handle v2 error payloads gracefully (e.g., missing API scope)
                if isinstance(data, dict) and data.get("error"):
                    msg = str(data.get("error"))
                    logging.getLogger(__name__).warning(f"Ahrefs v2 error: {msg}; returning mock sample")
                    runtime_flags.set_provider_error("ahrefs", msg)
                    metrics.inc("ahrefs_calls_mock")
                    return [
                        BacklinkRecord(url_from="https://example.com/article-1", url_to=target, title="Example Article 1", first_seen="2025-09-01", domain_rating=42),
                        BacklinkRecord(url_from="https://example.com/article-2", url_to=target, title="Example Article 2", first_seen="2025-09-02", domain_rating=13),
                    ]
                table = data.get("refpages") or data.get("backlinks") or data.get("anchors")
                # Some v2 responses wrap in 'refpages' for backlinks
                items = table if isinstance(table, list) else data.get("pages", [])
                results: List[BacklinkRecord] = []
                for item in items:
                    results.append(BacklinkRecord(
                        url_from=item.get("url_from") or item.get("referring_page") or item.get("url"),
                        url_to=item.get("url_to") or target,
                        title=item.get("title"),
                        first_seen=item.get("first_seen") or item.get("first_seen_link"),
                        domain_rating=item.get("domain_rating") or item.get("domain_rating_source"),
                    ))
                return results
            else:
                # v3 beta style (may require enterprise; keep attempt but be resilient)
                params = {
                    "target": target,
                    "mode": mode,
                    "limit": limit,
                    "aggregation": "all",
                    "history": "live"
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}
                try:
                    resp = await client.get(f"{self.base_url}{self.BASE_PATH}", params=params, headers=headers)
                    resp.raise_for_status()
                    data = resp.json() or {}
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Ahrefs v3 request failed; {e}")
                    runtime_flags.set_provider_error("ahrefs", "v3 request failed")
                    metrics.inc("ahrefs_calls_mock")
                    return [
                        BacklinkRecord(url_from="https://example.com/article-1", url_to=target, title="Example Article 1", first_seen="2025-09-01", domain_rating=42),
                        BacklinkRecord(url_from="https://example.com/article-2", url_to=target, title="Example Article 2", first_seen="2025-09-02", domain_rating=13),
                    ]
                results: List[BacklinkRecord] = []
                for item in data.get("data", []):
                    results.append(BacklinkRecord(
                        url_from=item.get("url_from"),
                        url_to=item.get("url_to", target),
                        title=item.get("title"),
                        first_seen=item.get("first_seen_link") or item.get("first_seen"),
                        domain_rating=item.get("domain_rating_source") or item.get("domain_rating"),
                    ))
                return results

ahrefs_client = AhrefsClient()
