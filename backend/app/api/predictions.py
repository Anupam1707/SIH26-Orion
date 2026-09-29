"""Serve immutable precomputed forecasts, gated by the current demo clock."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


@router.get('/atms')
def atms(request: Request) -> list[dict]:
    return request.app.state.demo.public.atms.to_dict('records')


@router.get('/prediction-cases')
def prediction_cases(request: Request) -> list[dict]:
    state = request.app.state.demo
    visible = state.public.complaints_upto(state.demo_clock)
    result = []
    for c in visible.iloc[::-1].itertuples():
        case = state.predictions['cases'].get(c.id)
        # Do not disclose a future scheduled prediction timestamp.
        ready = case is not None and datetime.fromisoformat(case['prediction_time']) <= state.demo_clock
        result.append({'id': c.id, 'amount_inr': c.amount_inr, 'ready': ready,
                       'prediction_time': case['prediction_time'] if ready else None})
    return result


@router.get('/predictions/{complaint_id}')
def predictions(complaint_id: str, request: Request,
                model: Literal['baseline', 'kde', 'xgboost'] = 'baseline',
                window: int = Query(default=6)) -> dict:
    if window not in (2, 6, 24):
        raise HTTPException(422, 'Window must be 2, 6 or 24 hours')
    state = request.app.state.demo
    if complaint_id not in set(state.public.complaints_upto(state.demo_clock).id):
        raise HTTPException(404, 'Complaint is not visible at the demo clock')
    case = state.predictions['cases'].get(complaint_id)
    if not case or datetime.fromisoformat(case['prediction_time']) > state.demo_clock:
        raise HTTPException(409, 'Prediction is not yet available at the demo clock')
    result = {key: value for key, value in case.items() if key != 'models'}
    return {**result, **case['models'][model][window], 'demo_clock': state.demo_clock.isoformat()}


@router.get('/evaluation')
def evaluation(request: Request) -> dict:
    state = request.app.state.demo
    report = state.predictions['evaluation'].get(state.demo_clock.isoformat())
    if report is None:
        raise HTTPException(409, 'Evaluation snapshot unavailable at this clock')
    return {**report, **state.predictions['metadata'], 'demo_clock': state.demo_clock.isoformat()}
