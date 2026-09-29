from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict:
    state = request.app.state.demo
    return {
        "status": "ok",
        "scenario_hash": state.manifest["scenario_hash"],
        "seed": state.manifest["seed"],
        "demo_clock": state.demo_clock.isoformat() if state.demo_clock else None,
    }
