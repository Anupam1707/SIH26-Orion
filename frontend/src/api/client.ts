/** Typed API client. All calls go through the dev-server proxy at /api. */

export interface Health {
  status: "ok";
  scenario_hash: string;
  seed: number;
  demo_clock: string | null;
}

async function get<T>(path: string, method = 'GET'): Promise<T> {
  const res = await fetch(`/api${path}`, { method });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export const api = {
  health: () => get<Health>("/health"),
  summary: () => get<Summary>('/summary'),
  complaints: () => get<Complaint[]>('/complaints'),
  districts: () => get<GeoJSON.FeatureCollection>('/districts'),
  trace: (id: string) => get<Trace>(`/cases/${encodeURIComponent(id)}/trace`),
  account: (id: string) => get<Account>(`/accounts/${encodeURIComponent(id)}`),
  start: () => get<{ complaint_id: string }>('/demo/start', 'POST'),
  reset: () => get('/demo/reset', 'POST'),
  predictionCases: () => get<PredictionCase[]>('/prediction-cases'),
  predictions: (id: string, model: ModelName, window: number) => get<Prediction>(`/predictions/${encodeURIComponent(id)}?model=${model}&window=${window}`),
  evaluation: () => get<Evaluation>('/evaluation'),
  // Phase 4: Alerts
  alerts: () => get<Alert[]>('/alerts'),
  ackAlert: (id: string) => get<Alert>(`/alerts/${encodeURIComponent(id)}/ack`, 'POST'),
  generateAlerts: (complaintId: string) => get<AlertGenResult>(`/alerts/generate/${encodeURIComponent(complaintId)}`, 'POST'),
  // Phase 4: Fund Blocking
  blockRecommendations: (complaintId: string) => get<BlockRecommendation>(`/block/${encodeURIComponent(complaintId)}`),
  simulateFreeze: (complaintId: string, accounts: string[]) =>
    fetch(`/api/block/${encodeURIComponent(complaintId)}/simulate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accounts }),
    }).then(res => { if (!res.ok) throw new Error(`POST failed: ${res.status}`); return res.json() as Promise<FreezeSimulation>; }),
};

export interface Summary {
  demo_clock: string; complaints: number; reported_amount_inr: number;
  observed_transactions: number; accounts_with_patterns: number; demo_running: boolean;
}
export interface Complaint {
  id: string; victim_account_id: string; amount_inr: number; incident_at: string;
  reported_at: string; district_id: string; description: string;
}
export interface Transaction {
  id: string; src: string; dst: string; amount_inr: number; ts: string; channel: string;
  hop?: number; traced_amount_inr?: number;
}
export interface Signal { name: string; reason: string; tx_ids: string[] }
export interface Account {
  id: string; bank: string; holder: string; home_district_id: string; risk: number;
  signals: Signal[]; transactions: Transaction[]; source_transactions: Transaction[];
}
export interface Trace {
  complaint: Complaint; demo_clock: string; attribution_note: string;
  nodes: { id: string; hop: number; inferred_role: string; risk: number; signals: Signal[] }[];
  edges: Transaction[]; hop_order: number[];
  patterns: { rule: string; flagged: string[]; tx_ids: string[]; detail: { reason: string } }[];
}

export type ModelName = 'baseline' | 'kde' | 'xgboost';
export interface PredictionCase { id: string; amount_inr: number; ready: boolean; prediction_time: string | null }
export interface PredictionReason { text: string; source_group: string; feature: string | null; contribution: number | null }
export interface PredictedAtm {
  id: string; lat: number; lng: number; bank: string; district_id: string;
  probability: number; reasons: PredictionReason[];
}
export interface Withdrawal { id: string; account_id: string; atm_id: string; amount_inr: number; ts: string }
export interface EvidenceAccount { id: string; bank: string; home_district_id: string; opened_at: string }
export interface Prediction {
  complaint_id: string; prediction_time: string; demo_clock: string; max_input_ts: string;
  model: ModelName; window_hours: number; fallback: string | null; probability_note: string;
  atms: PredictedAtm[]; chain_accounts: string[]; linked_accounts: string[]; holder_accounts: string[];
  training: { n: number; case_ids: string[]; bandwidth_km: number; available_at: string; latest_outcome_at: string | null; method: string };
  evidence: { transactions: Transaction[]; withdrawals: Withdrawal[]; accounts: EvidenceAccount[]; complaint: Complaint; temporal_population_n: number };
}
export interface EvaluationRow {
  model: ModelName; window_hours: number; strategy: string; n: number;
  hit_rate: number | null; hit_rate_ci95: [number, number] | null;
  precision_at_5: number | null; precision_ceiling: number | null; cases_with_cashout: number;
}
export interface Evaluation {
  rows: EvaluationRow[]; comparisons: { strategy: string; window_hours: number; n: number; beats_baseline: boolean; message: string }[];
  test_cases_total: number; test_cases_available: number; pending_cases: number;
  bootstrap_replicates: number; top_k: number; note: string; train_start: string; test_start: string;
  test_end: string; train_cases_n: number; fitted_train_cases_n: number; training_note: string;
  bandwidth_km: number; bandwidth_candidates_km: number[]; demo_clock: string;
}

// Phase 4: Alerts
export interface AlertChannel {
  type: string; label: string; recipient: string; status: string; delivered_at: string;
}
export interface Alert {
  id: string; complaint_id: string; created_at: string; severity: 'critical' | 'high' | 'medium';
  title: string; description: string; target_type: 'ATM' | 'account'; target_id: string;
  target_district: string; target_bank: string; probability: number; window_hours: number;
  model: string; case_amount_inr: number; rank: number; channels: AlertChannel[];
  status: 'triggered' | 'acknowledged'; acknowledged_at: string | null;
}
export interface AlertGenResult {
  complaint_id: string; new_alerts: number; total_alerts: number;
  alerts?: Alert[]; message?: string;
}

// Phase 4: Fund Blocking
export interface RecommendedAccount {
  id: string; reason: string; bank?: string; home_district_id?: string;
  inferred_role?: string; hop?: number; risk?: number;
}
export interface BlockRecommendation {
  complaint_id: string; demo_clock: string; recommended_accounts: RecommendedAccount[];
  money_reachable_before_inr: number; money_reachable_after_inr: number;
  prevented_inr: number; prevented_pct: number;
  trace_node_count: number; trace_edge_count: number; max_accounts: number;
}
export interface FreezeSimulation {
  accounts_frozen: string[]; complaint_id: string; demo_clock: string;
  money_reachable_before_inr: number; money_reachable_after_inr: number;
  prevented_inr: number; prevented_pct: number;
}
