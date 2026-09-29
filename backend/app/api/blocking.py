"""Fund blocking endpoints (spec §13): freeze recommendations and simulation."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.block.service import get_recommendations, run_simulation

router = APIRouter()


class SimulateRequest(BaseModel):
    accounts: list[str]


def _state(request: Request):
    return request.app.state.demo


@router.get("/block/{complaint_id}")
def block_recommendations(complaint_id: str, request: Request) -> dict:
    """Recommend accounts to freeze for a given case."""
    s = _state(request)

    visible = s.public.complaints_upto(s.demo_clock)
    complaint = visible[visible.id == complaint_id]
    if complaint.empty:
        raise HTTPException(404, "Complaint not visible at the demo clock")

    snapshot = s.analysis.get(s.demo_clock.isoformat())
    if snapshot is None:
        raise HTTPException(409, "Analysis snapshot unavailable at this clock")

    graph = s.graphs.get(s.demo_clock.isoformat())
    if graph is None:
        raise HTTPException(409, "Graph unavailable at this clock")

    return get_recommendations(
        s.public,
        graph,
        complaint.iloc[0].to_dict(),
        snapshot["risks"],
        s.demo_clock,
        s.config,
    )


@router.post("/block/{complaint_id}/simulate")
def simulate(complaint_id: str, body: SimulateRequest, request: Request) -> dict:
    """Simulate freezing specific accounts and return before/after metrics."""
    s = _state(request)

    visible = s.public.complaints_upto(s.demo_clock)
    complaint = visible[visible.id == complaint_id]
    if complaint.empty:
        raise HTTPException(404, "Complaint not visible at the demo clock")

    snapshot = s.analysis.get(s.demo_clock.isoformat())
    if snapshot is None:
        raise HTTPException(409, "Analysis snapshot unavailable at this clock")

    graph = s.graphs.get(s.demo_clock.isoformat())
    if graph is None:
        raise HTTPException(409, "Graph unavailable at this clock")

    result = run_simulation(
        s.public,
        graph,
        complaint.iloc[0].to_dict(),
        snapshot["risks"],
        s.config,
        body.accounts,
    )
    result["complaint_id"] = complaint_id
    result["demo_clock"] = s.demo_clock.isoformat()
    return result
