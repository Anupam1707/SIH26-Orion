/**
 * Typed API client.
 * Supports:
 * 1. Live FastAPI Backend (via local proxy or VITE_API_BASE_URL)
 * 2. Instant Standalone Demo Mode (for zero-dependency Vercel deployment)
 */

import { demoService } from "./demoService";

export interface Health {
  status: "ok";
  scenario_hash: string;
  seed: number;
  demo_clock: string | null;
  mode?: "live" | "simulated";
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

let connectionMode: "checking" | "live" | "simulated" = "checking";
let healthCheckPromise: Promise<boolean> | null = null;

async function checkBackendAvailability(): Promise<boolean> {
  if (healthCheckPromise) return healthCheckPromise;

  healthCheckPromise = (async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${API_BASE_URL}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        connectionMode = "live";
        return true;
      }
    } catch {
      // Backend not reachable, fall back to simulated demo mode
    }
    connectionMode = "simulated";
    return false;
  })();

  return healthCheckPromise;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const isLive = await checkBackendAvailability();

  if (isLive) {
    try {
      const res = await fetch(`${API_BASE_URL}${path}`, options);
      if (!res.ok) throw new Error(`${options?.method || "GET"} ${path} failed: ${res.status}`);
      return (await res.json()) as T;
    } catch (err) {
      // If live backend suddenly fails, fall back to demo service
      console.warn(`[ORION] Backend request to ${path} failed, falling back to demo service:`, err);
      connectionMode = "simulated";
    }
  }

  // Route to demo service
  return handleDemoFallback<T>(path, options);
}

// Router for simulated demo responses
async function handleDemoFallback<T>(path: string, options?: RequestInit): Promise<T> {
  const method = options?.method || "GET";
  const url = new URL(path, "http://dummy");
  const pathname = url.pathname;

  if (pathname === "/health") {
    const h = await demoService.health();
    return { ...h, mode: "simulated" } as unknown as T;
  }
  if (pathname === "/summary") {
    return (await demoService.summary()) as unknown as T;
  }
  if (pathname === "/complaints") {
    return (await demoService.complaints()) as unknown as T;
  }
  if (pathname === "/districts") {
    return (await demoService.districts()) as unknown as T;
  }
  if (pathname.startsWith("/cases/") && pathname.endsWith("/trace")) {
    const id = decodeURIComponent(pathname.replace("/cases/", "").replace("/trace", ""));
    return (await demoService.trace(id)) as unknown as T;
  }
  if (pathname.startsWith("/accounts/")) {
    const id = decodeURIComponent(pathname.replace("/accounts/", ""));
    return (await demoService.account(id)) as unknown as T;
  }
  if (pathname === "/demo/start" && method === "POST") {
    return (await demoService.start()) as unknown as T;
  }
  if (pathname === "/demo/reset" && method === "POST") {
    return (await demoService.reset()) as unknown as T;
  }
  if (pathname === "/prediction-cases") {
    return (await demoService.predictionCases()) as unknown as T;
  }
  if (pathname.startsWith("/predictions/")) {
    const id = decodeURIComponent(pathname.replace("/predictions/", ""));
    const model = (url.searchParams.get("model") || "baseline") as ModelName;
    const window = parseInt(url.searchParams.get("window") || "6", 10);
    return (await demoService.predictions(id, model, window)) as unknown as T;
  }
  if (pathname === "/evaluation") {
    return (await demoService.evaluation()) as unknown as T;
  }
  if (pathname === "/alerts" && method === "GET") {
    return (await demoService.alerts()) as unknown as T;
  }
  if (pathname.startsWith("/alerts/") && pathname.endsWith("/ack") && method === "POST") {
    const id = decodeURIComponent(pathname.replace("/alerts/", "").replace("/ack", ""));
    return (await demoService.ackAlert(id)) as unknown as T;
  }
  if (pathname.startsWith("/alerts/generate/") && method === "POST") {
    const id = decodeURIComponent(pathname.replace("/alerts/generate/", ""));
    return (await demoService.generateAlerts(id)) as unknown as T;
  }
  if (pathname.startsWith("/block/") && pathname.endsWith("/simulate") && method === "POST") {
    const id = decodeURIComponent(pathname.replace("/block/", "").replace("/simulate", ""));
    const body = options?.body ? JSON.parse(options.body as string) : { accounts: [] };
    return (await demoService.simulateFreeze(id, body.accounts || [])) as unknown as T;
  }
  if (pathname.startsWith("/block/")) {
    const id = decodeURIComponent(pathname.replace("/block/", ""));
    return (await demoService.blockRecommendations(id)) as unknown as T;
  }
  if (pathname === "/adversary/curves") {
    return (await demoService.adversaryCurves()) as unknown as T;
  }
  if (pathname === "/adversary/run" && method === "POST") {
    const body = options?.body ? JSON.parse(options.body as string) : {};
    return (await demoService.adversaryRun(body.complaint_id, body.hardened)) as unknown as T;
  }

  throw new Error(`Unhandled demo fallback path: ${path}`);
}

export const api = {
  getMode: () => connectionMode,
  health: () => request<Health>("/health"),
  summary: () => request<Summary>("/summary"),
  complaints: () => request<Complaint[]>("/complaints"),
  districts: () => request<GeoJSON.FeatureCollection>("/districts"),
  trace: (id: string) => request<Trace>(`/cases/${encodeURIComponent(id)}/trace`),
  account: (id: string) => request<Account>(`/accounts/${encodeURIComponent(id)}`),
  start: () => request<{ complaint_id: string; demo_clock?: string }>("/demo/start", { method: "POST" }),
  reset: () => request<{ demo_clock: string }>("/demo/reset", { method: "POST" }),
  predictionCases: () => request<PredictionCase[]>("/prediction-cases"),
  predictions: (id: string, model: ModelName, window: number) =>
    request<Prediction>(`/predictions/${encodeURIComponent(id)}?model=${model}&window=${window}`),
  evaluation: () => request<Evaluation>("/evaluation"),
  // Phase 4: Alerts
  alerts: () => request<Alert[]>("/alerts"),
  ackAlert: (id: string) => request<Alert>(`/alerts/${encodeURIComponent(id)}/ack`, { method: "POST" }),
  generateAlerts: (complaintId: string) =>
    request<AlertGenResult>(`/alerts/generate/${encodeURIComponent(complaintId)}`, { method: "POST" }),
  // Phase 4: Fund Blocking
  blockRecommendations: (complaintId: string) => request<BlockRecommendation>(`/block/${encodeURIComponent(complaintId)}`),
  simulateFreeze: (complaintId: string, accounts: string[]) =>
    request<FreezeSimulation>(`/block/${encodeURIComponent(complaintId)}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ accounts }),
    }),
  // Phase 5: Adversary Lab
  adversaryCurves: () => request<AdversaryCurvesResponse>("/adversary/curves"),
  adversaryRun: (complaintId?: string, hardened?: boolean) =>
    request<AdversaryRunResult>("/adversary/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId, hardened: hardened ?? false }),
    }),
};

export interface Summary {
  demo_clock: string;
  complaints: number;
  reported_amount_inr: number;
  observed_transactions: number;
  accounts_with_patterns: number;
  demo_running: boolean;
}
export interface Complaint {
  id: string;
  victim_account_id: string;
  amount_inr: number;
  incident_at: string;
  reported_at: string;
  district_id: string;
  description: string;
}
export interface Transaction {
  id: string;
  src: string;
  dst: string;
  amount_inr: number;
  ts: string;
  channel: string;
  hop?: number;
  traced_amount_inr?: number;
}
export interface Signal {
  name: string;
  reason: string;
  tx_ids: string[];
}
export interface Account {
  id: string;
  bank: string;
  holder: string;
  home_district_id: string;
  risk: number;
  signals: Signal[];
  transactions: Transaction[];
  source_transactions: Transaction[];
}
export interface Trace {
  complaint: Complaint;
  demo_clock: string;
  attribution_note: string;
  nodes: { id: string; hop: number; inferred_role: string; risk: number; signals: Signal[] }[];
  edges: Transaction[];
  hop_order: number[];
  patterns: { rule: string; flagged: string[]; tx_ids: string[]; detail: { reason: string } }[];
}

export type ModelName = "baseline" | "kde" | "xgboost";
export interface PredictionCase {
  id: string;
  amount_inr: number;
  ready: boolean;
  prediction_time: string | null;
}
export interface PredictionReason {
  text: string;
  source_group: string;
  feature: string | null;
  contribution: number | null;
}
export interface PredictedAtm {
  id: string;
  lat: number;
  lng: number;
  bank: string;
  district_id: string;
  probability: number;
  reasons: PredictionReason[];
}
export interface Withdrawal {
  id: string;
  account_id: string;
  atm_id: string;
  amount_inr: number;
  ts: string;
}
export interface EvidenceAccount {
  id: string;
  bank: string;
  home_district_id: string;
  opened_at: string;
}
export interface Prediction {
  complaint_id: string;
  prediction_time: string;
  demo_clock: string;
  max_input_ts: string;
  model: ModelName;
  window_hours: number;
  fallback: string | null;
  probability_note: string;
  atms: PredictedAtm[];
  chain_accounts: string[];
  linked_accounts: string[];
  holder_accounts: string[];
  training: {
    n: number;
    case_ids: string[];
    bandwidth_km: number;
    available_at: string;
    latest_outcome_at: string | null;
    method: string;
  };
  evidence: {
    transactions: Transaction[];
    withdrawals: Withdrawal[];
    accounts: EvidenceAccount[];
    complaint: Complaint;
    temporal_population_n: number;
  };
}
export interface EvaluationRow {
  model: ModelName;
  window_hours: number;
  strategy: string;
  n: number;
  hit_rate: number | null;
  hit_rate_ci95: [number, number] | null;
  precision_at_5: number | null;
  precision_ceiling: number | null;
  cases_with_cashout: number;
}
export interface Evaluation {
  rows: EvaluationRow[];
  comparisons: { strategy: string; window_hours: number; n: number; beats_baseline: boolean; message: string }[];
  test_cases_total: number;
  test_cases_available: number;
  pending_cases: number;
  bootstrap_replicates: number;
  top_k: number;
  note: string;
  train_start: string;
  test_start: string;
  test_end: string;
  train_cases_n: number;
  fitted_train_cases_n: number;
  training_note: string;
  bandwidth_km: number;
  bandwidth_candidates_km: number[];
  demo_clock: string;
}

// Phase 4: Alerts
export interface AlertChannel {
  type: string;
  label: string;
  recipient: string;
  status: string;
  delivered_at: string;
}
export interface Alert {
  id: string;
  complaint_id: string;
  created_at: string;
  severity: "critical" | "high" | "medium";
  title: string;
  description: string;
  target_type: "ATM" | "account";
  target_id: string;
  target_district: string;
  target_bank: string;
  probability: number;
  window_hours: number;
  model: string;
  case_amount_inr: number;
  rank: number;
  channels: AlertChannel[];
  status: "triggered" | "acknowledged";
  acknowledged_at: string | null;
}
export interface AlertGenResult {
  complaint_id: string;
  new_alerts: number;
  total_alerts: number;
  alerts?: Alert[];
  message?: string;
}

// Phase 4: Fund Blocking
export interface RecommendedAccount {
  id: string;
  reason: string;
  bank?: string;
  home_district_id?: string;
  inferred_role?: string;
  hop?: number;
  risk?: number;
}
export interface BlockRecommendation {
  complaint_id: string;
  demo_clock: string;
  recommended_accounts: RecommendedAccount[];
  money_reachable_before_inr: number;
  money_reachable_after_inr: number;
  prevented_inr: number;
  prevented_pct: number;
  trace_node_count: number;
  trace_edge_count: number;
  max_accounts: number;
}
export interface FreezeSimulation {
  accounts_frozen: string[];
  complaint_id: string;
  demo_clock: string;
  money_reachable_before_inr: number;
  money_reachable_after_inr: number;
  prevented_inr: number;
  prevented_pct: number;
}

// Phase 5: Adversary Lab
export interface AdversaryMove {
  step: number;
  move: "switch_atm" | "delay" | "add_mule_hop" | "split_amount";
  description: string;
  cost: number;
  cumulative_cost: number;
  target_atms: string[];
  top5_atms: string[];
  detection_prob: number;
  detected: boolean;
}

export interface AdversaryRunResult {
  complaint_id: string;
  hardened: boolean;
  initial_detected: boolean;
  final_detected: boolean;
  total_cost: number;
  initial_probability: number;
  final_probability: number;
  moves_count: number;
  moves: AdversaryMove[];
}

export interface CurvePoint {
  budget: number;
  detection_rate: number;
  detected_count: number;
}

export interface AdversaryCurvesResponse {
  budgets: number[];
  baseline_curve: CurvePoint[];
  hardened_curve: CurvePoint[];
  test_cases_count: number;
  target_window: string;
  summary: string;
}
