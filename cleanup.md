# Cleanup & Security Hardening Guide (Temporary)

This file documents the one-time cleanup and security pass. It will be removed after execution.

## Objectives
- Remove unused dependencies and code paths.
- Ensure runtime toggle + provider clients are the only source of truth for external calls.
- Tighten .env usage and secrets handling.
- Run quick local quality gates and a lightweight security scan.

## Inventory Findings
- Unused dependencies referenced but not used in code: pandas, numpy, celery, aioredis, swagger-ui-bundle, orjson, python-dateutil, slowapi (we ship a custom in-memory limiter instead). Keep structlog.
- Duplicate/legacy clients under `app/services/ahrefs_client.py` (older) vs `app/services/external/ahrefs_client.py` (current). Keep the latter and remove the older.
- Persistent rate limiter migration stub exists but no usage (keep for future if needed).
- Frontend compiled assets under `.next/` are ignored and fine.

## Actions
1) Remove legacy client file to prevent confusion:
   - Delete `src/backend/app/services/ahrefs_client.py` (keep `src/backend/app/services/external/ahrefs_client.py`).

2) Deps pruning plan (defer actual removal to a dedicated PR once tests confirm):
   - Consider removing from `requirements.txt` if confirmed unused: pandas, numpy, celery, kombu, aioredis, swagger-ui-bundle, orjson, python-dateutil, slowapi. Retain only when code paths exist.

3) Auth/CORS checks:
   - Ensure CORS is restricted to localhost during dev via settings; production to be configured via env.
   - Header-based dev auth already in place; enforce with `ENFORCE_AUTH_HEADERS=1` for staging.

4) Secrets hygiene:
   - `.env` is in `.gitignore`; ensure no secrets are committed. No hardcoded provider credentials in repo.

5) Security scan (manual quick pass):
   - Search for `token=`, `apikey`, `Authorization:` strings in repo; ensure none are committed.
   - Confirm provider error messages do not leak secrets (they don’t; only status codes / short text).

6) Runtime toggle verification:
   - GET /api/v1/runtime/config -> expect `{ mock_mode: true }` by default.
   - POST /api/v1/runtime/config { mock_mode: false } -> observe UI message explaining provider issues, then set back to true.

7) Minimal tests to run locally:
   - Backend import check & lint (fast).
   - Start backend and GET /api/v1/health.
   - Start frontend and load dashboard; verify campaigns render and toggle works.

## Done
- [x] Marked legacy client file for deletion.
- [x] Updated docs to reflect Mock/Live toggle and example campaigns.
- [ ] Deps pruning deferred to follow-up after confirmation.

-- End of temporary guide --
