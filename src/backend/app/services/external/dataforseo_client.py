"""DataForSEO API client (skeleton) supporting backlinks & SERP mock modes."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import base64
import httpx
from datetime import datetime, timezone
from app.core.metrics import metrics
from config.settings import settings as _settings
from config.settings import settings
from app.core.rate_limiter import dataforseo_limiter
import logging
from app.core.runtime_flags import runtime_flags

@dataclass
class BacklinkRecord:
    url_from: str
    url_to: str
    title: Optional[str]
    first_seen: Optional[str]
    domain_rating: Optional[int]
    source_api: str = "dataforseo"

@dataclass
class SerpResult:
    keyword: str
    url: str
    position: int
    page_title: Optional[str]

class DataForSeoClient:
    BACKLINK_PATH = "/backlinks/backlinks/live"
    SERP_PATH = "/serp/google/organic/live/regular"

    def __init__(self):
        self.username = settings.dataforseo_username or settings.DATAFORSEO_USERNAME
        self.password = settings.dataforseo_password or settings.DATAFORSEO_PASSWORD
        self.base_url = settings.dataforseo_base_url.rstrip('/')

    def _auth_header(self) -> dict:
        if not self.username or not self.password:
            return {}
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    async def fetch_backlinks(self, target: str, limit: int = 50) -> List[BacklinkRecord]:
        # Force mock when runtime flag is enabled
        if runtime_flags.is_mock_mode():
            metrics.inc("dataforseo_backlink_calls_mock")
            return [
                BacklinkRecord(url_from="https://news.example.net/story-a", url_to=target, title="Story A", first_seen="2025-09-03", domain_rating=55),
                BacklinkRecord(url_from="https://blog.sample.io/post-b", url_to=target, title="Post B", first_seen="2025-09-04", domain_rating=12),
            ]
        # Monitoring window guard (UTC assumption until TZ logic added)
        now_utc = datetime.now(timezone.utc)
        try:
            start_h = getattr(_settings, 'monitor_start_hour', 0) or 0
            end_h = getattr(_settings, 'monitor_end_hour', 23) or 23
            if not (start_h <= now_utc.hour <= end_h):
                metrics.inc("monitor_window_skips")
                return []
        except Exception:
            pass
        if not dataforseo_limiter.allow():
            metrics.inc("dataforseo_rate_limit_drops")
            logging.getLogger(__name__).warning("DataForSEO backlink rate limited; returning empty list")
            return []
        if not self.username or not self.password:
            metrics.inc("dataforseo_backlink_calls_mock")
            return [
                BacklinkRecord(url_from="https://news.example.net/story-a", url_to=target, title="Story A", first_seen="2025-09-03", domain_rating=55),
                BacklinkRecord(url_from="https://blog.sample.io/post-b", url_to=target, title="Post B", first_seen="2025-09-04", domain_rating=12),
            ]
        # Cost budget guard (simple per-call estimate)
        try:
            gauges = metrics.snapshot().get("gauges", {})
            current_cost = gauges.get("cost_estimated_spend_usd", 0.0)
            per_call_cost = 0.01  # USD heuristic
            if current_cost + per_call_cost > getattr(_settings, 'cost_budget_daily_usd', 9999):
                metrics.inc("cost_budget_skips")
                return []
        except Exception:
            pass
        payload = [{"target": target, "limit": limit}]
        metrics.inc("dataforseo_backlink_calls_real")
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(f"{self.base_url}{self.BACKLINK_PATH}", headers=self._auth_header(), json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logging.getLogger(__name__).warning(f"DataForSEO backlinks request failed; {e}")
                runtime_flags.set_provider_error("dataforseo", "HTTP error on backlinks")
                metrics.inc("dataforseo_backlink_calls_mock")
                return [
                    BacklinkRecord(url_from="https://news.example.net/story-a", url_to=target, title="Story A", first_seen="2025-09-03", domain_rating=55),
                    BacklinkRecord(url_from="https://blog.sample.io/post-b", url_to=target, title="Post B", first_seen="2025-09-04", domain_rating=12),
                ]
            if isinstance(data, dict):
                sc = data.get("status_code")
                # 402xx and 401xx are common for access/subscription issues
                if sc and int(sc) >= 40000:
                    msg = f"Access issue status_code={sc}"
                    logging.getLogger(__name__).warning(f"DataForSEO {msg}; using mock sample")
                    runtime_flags.set_provider_error("dataforseo", msg)
                    metrics.inc("dataforseo_backlink_calls_mock")
                    return [
                        BacklinkRecord(url_from="https://news.example.net/story-a", url_to=target, title="Story A", first_seen="2025-09-03", domain_rating=55),
                        BacklinkRecord(url_from="https://blog.sample.io/post-b", url_to=target, title="Post B", first_seen="2025-09-04", domain_rating=12),
                    ]
        # Update cost gauge optimistically
        try:
            gauges = metrics.snapshot().get("gauges", {})
            new_cost = gauges.get("cost_estimated_spend_usd", 0.0) + 0.01
            metrics.set_gauge("cost_estimated_spend_usd", new_cost)
        except Exception:
            pass
        results = []
        # DataForSEO v3 often returns { tasks: [ { result: [ { items: [...] } ] } ] }
        try:
            tasks = data.get("tasks") if isinstance(data, dict) else data
        except Exception:
            tasks = data
        if isinstance(tasks, list):
            for task in tasks:
                result_blocks = []
                if isinstance(task, dict):
                    result_blocks = task.get("result", []) or []
                for block in (result_blocks if isinstance(result_blocks, list) else []):
                    items = block.get("items", []) if isinstance(block, dict) else []
                    for item in items[:limit]:
                        results.append(BacklinkRecord(
                            url_from=item.get("url_from"),
                            url_to=item.get("url_to", target),
                            title=item.get("title"),
                            first_seen=item.get("first_seen"),
                            domain_rating=item.get("domain_rating"),
                        ))
        # Fallback: previous flat shape
        if not results and isinstance(data, list):
            for task in data:
                for item in task.get("result", [])[:limit]:
                    results.append(BacklinkRecord(
                        url_from=item.get("url_from"),
                        url_to=item.get("url_to", target),
                        title=item.get("title"),
                        first_seen=item.get("first_seen"),
                        domain_rating=item.get("domain_rating")
                    ))
        return results

    async def fetch_serp(self, keyword: str, top_n: int = 20) -> List[SerpResult]:
        if runtime_flags.is_mock_mode():
            metrics.inc("dataforseo_serp_calls_mock")
            return [
                SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-1", position=1, page_title=f"{keyword} Result 1"),
                SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-2", position=2, page_title=f"{keyword} Result 2"),
            ]
        # Monitoring window guard
        now_utc = datetime.now(timezone.utc)
        try:
            start_h = getattr(_settings, 'monitor_start_hour', 0) or 0
            end_h = getattr(_settings, 'monitor_end_hour', 23) or 23
            if not (start_h <= now_utc.hour <= end_h):
                metrics.inc("monitor_window_skips")
                return []
        except Exception:
            pass
        if not dataforseo_limiter.allow():
            metrics.inc("dataforseo_rate_limit_drops")
            logging.getLogger(__name__).warning("DataForSEO SERP rate limited; returning empty SERP list")
            return []
        if not self.username or not self.password:
            metrics.inc("dataforseo_serp_calls_mock")
            return [
                SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-1", position=1, page_title=f"{keyword} Result 1"),
                SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-2", position=2, page_title=f"{keyword} Result 2"),
            ]
        # Cost budget guard
        try:
            gauges = metrics.snapshot().get("gauges", {})
            current_cost = gauges.get("cost_estimated_spend_usd", 0.0)
            per_call_cost = 0.02  # SERP typically a bit more expensive
            if current_cost + per_call_cost > getattr(_settings, 'cost_budget_daily_usd', 9999):
                metrics.inc("cost_budget_skips")
                return []
        except Exception:
            pass
        payload = [{"keyword": keyword, "limit": top_n}]
        metrics.inc("dataforseo_serp_calls_real")
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(f"{self.base_url}{self.SERP_PATH}", headers=self._auth_header(), json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logging.getLogger(__name__).warning(f"DataForSEO SERP request failed; {e}")
                runtime_flags.set_provider_error("dataforseo", "HTTP error on SERP")
                metrics.inc("dataforseo_serp_calls_mock")
                return [
                    SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-1", position=1, page_title=f"{keyword} Result 1"),
                    SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-2", position=2, page_title=f"{keyword} Result 2"),
                ]
            if isinstance(data, dict):
                sc = data.get("status_code")
                if sc and int(sc) >= 40000:
                    msg = f"SERP access issue status_code={sc}"
                    logging.getLogger(__name__).warning(f"DataForSEO {msg}; returning mock SERP items")
                    runtime_flags.set_provider_error("dataforseo", msg)
                    metrics.inc("dataforseo_serp_calls_mock")
                    return [
                        SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-1", position=1, page_title=f"{keyword} Result 1"),
                        SerpResult(keyword=keyword, url=f"https://example-serp.com/{keyword}-2", position=2, page_title=f"{keyword} Result 2"),
                    ]
        try:
            gauges = metrics.snapshot().get("gauges", {})
            new_cost = gauges.get("cost_estimated_spend_usd", 0.0) + 0.02
            metrics.set_gauge("cost_estimated_spend_usd", new_cost)
        except Exception:
            pass
        results: List[SerpResult] = []
        try:
            tasks = data.get("tasks") if isinstance(data, dict) else data
        except Exception:
            tasks = data
        if isinstance(tasks, list):
            for task in tasks:
                result_blocks = task.get("result", []) if isinstance(task, dict) else []
                for block in (result_blocks if isinstance(result_blocks, list) else []):
                    items = block.get("items", []) if isinstance(block, dict) else []
                    for item in items[:top_n]:
                        results.append(SerpResult(
                            keyword=keyword,
                            url=item.get("url"),
                            position=item.get("rank", 0),
                            page_title=item.get("title")
                        ))
        if not results and isinstance(data, list):
            for task in data:
                for item in task.get("result", [])[:top_n]:
                    results.append(SerpResult(
                        keyword=keyword,
                        url=item.get("url"),
                        position=item.get("rank", 0),
                        page_title=item.get("title")
                    ))
        return results

dataforseo_client = DataForSeoClient()
