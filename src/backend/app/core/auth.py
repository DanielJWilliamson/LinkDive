"""Lightweight authentication dependency.

Transitional phase logic:
1. If X-User-Email header provided -> trust & normalize.
2. Else if strict auth NOT enabled -> fallback to legacy demo user.
3. Else raise 401.

You can enable strict header enforcement by setting environment variable
ENFORCE_AUTH_HEADERS=1 (e.g. in production deployment once real auth lands).

Rationale: Tests and current dev workflows expect a default user so we avoid
friction while scaffolding full OAuth / user persistence.
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import os

# Environment flag to force header requirement (opt-in strict mode)
STRICT_AUTH = os.getenv("ENFORCE_AUTH_HEADERS") == "1"

async def get_current_user(x_user_email: Optional[str] = Header(None, alias="X-User-Email")) -> str:
    """Resolve current user identity.

    - Accept explicit header (normalized to lowercase, trimmed).
    - If header missing and strict mode disabled -> return demo user.
    - If strict mode enabled and header missing -> 401.
    """
    if x_user_email and x_user_email.strip():
        return x_user_email.strip().lower()
    if not STRICT_AUTH:
        return "demo@linkdive.ai"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication header"
    )
