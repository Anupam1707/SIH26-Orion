"""API endpoints for Adversary Lab (spec §11, §13)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.adversary.service import get_adversary_curves, run_adversary_simulation

router = APIRouter(prefix="/adversary", tags=["adversary"])


class RunAdversaryRequest(BaseModel):
    complaint_id: str | None = None
    hardened: bool = False


@router.post("/run")
def run_adversary(req: RunAdversaryRequest, request: Request) -> dict[str, Any]:
    """Run greedy evasion search on a case and return the move log and results."""
    state = request.app.state.demo
    try:
        return run_adversary_simulation(state, complaint_id=req.complaint_id, hardened=req.hardened)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/curves")
def curves(request: Request) -> dict[str, Any]:
    """Return evasion cost curves over the test set for baseline and hardened models."""
    state = request.app.state.demo
    try:
        return get_adversary_curves(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
