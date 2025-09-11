"""Runtime configuration endpoints (mock/live toggle and provider diagnostics)."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.runtime_flags import runtime_flags
from app.core.auth import get_current_user


class RuntimeConfig(BaseModel):
    mock_mode: bool
    provider_errors: dict[str, str] = {}


class UpdateRuntimeConfig(BaseModel):
    mock_mode: bool


router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/config", response_model=RuntimeConfig)
async def get_runtime_config(current_user: str = Depends(get_current_user)):
    return RuntimeConfig(
        mock_mode=runtime_flags.is_mock_mode(),
        provider_errors=runtime_flags.get_provider_errors(),
    )


@router.post("/config", response_model=RuntimeConfig)
async def update_runtime_config(payload: UpdateRuntimeConfig, current_user: str = Depends(get_current_user)):
    runtime_flags.set_mock_mode(payload.mock_mode)
    return RuntimeConfig(
        mock_mode=runtime_flags.is_mock_mode(),
        provider_errors=runtime_flags.get_provider_errors(),
    )
