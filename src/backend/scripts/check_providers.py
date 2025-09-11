import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.external.ahrefs_client import AhrefsClient
from app.services.external.dataforseo_client import DataForSeoClient
from config.settings import settings
import httpx
import base64

async def main():
    target_url = "https://openai.com"
    target_domain = "openai.com"
    print("Settings summary:")
    print("- AHREFS_BASE_URL:", settings.ahrefs_base_url)
    print("- AHREFS_API_KEY present:", bool(settings.AHREFS_API_KEY or settings.ahrefs_api_key))
    print("- DATAFORSEO_BASE_URL:", settings.dataforseo_base_url)
    print("- DATAFORSEO creds present:", bool((settings.DATAFORSEO_USERNAME or settings.dataforseo_username) and (settings.DATAFORSEO_PASSWORD or settings.dataforseo_password)))

    ahrefs = AhrefsClient()
    dfs = DataForSeoClient()

    print("\nTesting Ahrefs backlinks...")
    try:
        res = await ahrefs.fetch_backlinks(target=target_url, limit=5)
        print(f"Ahrefs returned {len(res)} items")
        for r in res[:3]:
            print("-", r)
    except Exception as e:
        print("Ahrefs error:", e)

    # Raw Ahrefs v2 probe
    try:
        if "apiv2.ahrefs.com" in settings.ahrefs_base_url:
            # double-encode target for v2 when using prefix/exact
            from urllib.parse import quote
            target_enc = quote(quote(target_domain, safe=""), safe="")
            params = {
                "from": "backlinks",
                "target": target_enc,
                "mode": "domain",
                "limit": "3",
                "output": "json",
                "token": settings.AHREFS_API_KEY or settings.ahrefs_api_key,
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(settings.ahrefs_base_url, params=params)
                print("Ahrefs v2 raw status:", resp.status_code)
                data = resp.json()
                if isinstance(data, dict):
                    print("Ahrefs v2 fields:", list(data.keys())[:5])
                    print("Ahrefs v2 error:", data.get("error"))
    except Exception as e:
        print("Ahrefs v2 raw error:", e)

    print("\nTesting DataForSEO backlinks...")
    try:
        res = await dfs.fetch_backlinks(target=target_url, limit=5)
        print(f"DataForSEO returned {len(res)} items")
        for r in res[:3]:
            print("-", r)
    except Exception as e:
        print("DataForSEO error:", e)

    # Raw DataForSEO probe
    try:
        auth = base64.b64encode(f"{settings.DATAFORSEO_USERNAME or settings.dataforseo_username}:{settings.DATAFORSEO_PASSWORD or settings.dataforseo_password}".encode()).decode()
        payload = [{"target": target_domain, "mode": "as_is", "limit": 3}]
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{settings.dataforseo_base_url.rstrip('/')}/backlinks/backlinks/live", headers={"Authorization": f"Basic {auth}"}, json=payload)
            print("DataForSEO raw status:", resp.status_code)
            data = resp.json()
            if isinstance(data, dict):
                print("DFS fields:", list(data.keys())[:6])
                print("DFS status_code:", data.get("status_code"))
                print("DFS tasks_count:", data.get("tasks_count"))
                tasks = data.get("tasks") or []
                if tasks:
                    print("DFS task status:", tasks[0].get("status_code"), tasks[0].get("status_message"))
                    res0 = (tasks[0].get("result") or [])
                    if res0:
                        print("DFS result items_count:", res0[0].get("items_count"))
    except Exception as e:
        print("DataForSEO raw error:", e)

if __name__ == "__main__":
    asyncio.run(main())
