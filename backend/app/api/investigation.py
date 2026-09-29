"""Phase 2 investigation endpoints, all bounded by the demo clock."""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from app.graph.trace import trace_case

router = APIRouter()


def records(frame):
    return [{k: v.isoformat() if isinstance(v, datetime) else v for k, v in row.items()
             if k not in ('t', 'reported_t')} for row in frame.to_dict('records')]


def state(request):
    return request.app.state.demo


@router.get('/summary')
def summary(request: Request):
    s = state(request)
    complaints = s.public.complaints_upto(s.demo_clock)
    snapshot = s.analysis[s.demo_clock.isoformat()]
    return {'demo_clock': s.demo_clock.isoformat(), 'complaints': len(complaints),
            'reported_amount_inr': int(complaints.amount_inr.sum()),
            'observed_transactions': len(s.public.tx_upto(s.demo_clock)),
            'accounts_with_patterns': sum(bool(r['rules']) for r in snapshot['risks'].values()),
            'demo_running': s.demo_running}


@router.get('/complaints')
def complaints(request: Request):
    s = state(request)
    return records(s.public.complaints_upto(s.demo_clock).iloc[::-1])


@router.get('/cases/{complaint_id}/trace')
def trace(complaint_id: str, request: Request):
    s = state(request)
    visible = s.public.complaints_upto(s.demo_clock)
    complaint = visible[visible.id == complaint_id]
    if complaint.empty:
        raise HTTPException(404, 'Complaint is not visible at the demo clock')
    snapshot = s.analysis[s.demo_clock.isoformat()]
    result = trace_case(s.graphs[s.demo_clock.isoformat()], complaint.iloc[0].to_dict(), snapshot['risks'],
                        s.config.trace_max_hops, s.config.trace_min_share)
    ids = {n['id'] for n in result['nodes']}
    result['patterns'] = [m for m in snapshot['matches'] if ids.intersection(m['flagged'])]
    result['demo_clock'] = s.demo_clock.isoformat()
    result['risk_normalization_p99'] = snapshot['p99']
    return result


@router.get('/accounts/{account_id}')
def account(account_id: str, request: Request):
    s = state(request)
    accounts = s.public.accounts
    found = accounts[(accounts.id == account_id) & (accounts.opened_at <= s.demo_clock)]
    if found.empty:
        raise HTTPException(404, 'Unknown account')
    tx = s.public.tx_upto(s.demo_clock)
    detail = records(found)[0]
    detail['holder'] = s.public.persons.set_index('id').loc[detail['holder_id'], 'name']
    detail.update(s.analysis[s.demo_clock.isoformat()]['risks'][account_id])
    detail['transactions'] = records(tx[(tx.src == account_id) | (tx.dst == account_id)])
    evidence = {tid for signal in detail['signals'] for tid in signal['tx_ids']}
    detail['source_transactions'] = records(tx[tx.id.isin(evidence)])
    detail['demo_clock'] = s.demo_clock.isoformat()
    return detail


@router.post('/demo/start')
def start(request: Request):
    s = state(request)
    # Phase 2 preview: advance to observed complete trace. Guided story arrives in Phase 6.
    s.demo_clock = datetime.fromisoformat(s.manifest['trace_clock'])
    s.demo_running = True
    return {'complaint_id': s.manifest['demo_complaint_id'], 'demo_clock': s.demo_clock.isoformat()}


@router.post('/demo/reset')
def reset(request: Request):
    s = state(request)
    s.reset()
    return {'demo_clock': s.demo_clock.isoformat()}
