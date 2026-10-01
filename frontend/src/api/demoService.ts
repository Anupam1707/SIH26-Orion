import type {
  Account,
  AdversaryCurvesResponse,
  AdversaryRunResult,
  Alert,
  AlertGenResult,
  BlockRecommendation,
  Complaint,
  Evaluation,
  FreezeSimulation,
  Health,
  ModelName,
  Prediction,
  PredictionCase,
  Summary,
  Trace,
} from "./client";

interface DemoDataStore {
  demo_complaint_id: string;
  districts: GeoJSON.FeatureCollection;
  evaluation: Evaluation;
  curves: AdversaryCurvesResponse;
  initial: {
    health: Health;
    summary: Summary;
    complaints: Complaint[];
    prediction_cases: PredictionCase[];
    alerts: Alert[];
  };
  started: {
    health: Health;
    summary: Summary;
    complaints: Complaint[];
    prediction_cases: PredictionCase[];
    alerts: Alert[];
  };
  traces: Record<string, Trace>;
  accounts: Record<string, Account>;
  block_recs: Record<string, BlockRecommendation>;
  predictions: Record<string, Prediction>;
  adversary: {
    baseline: AdversaryRunResult;
    hardened: AdversaryRunResult;
  };
}

class DemoService {
  private data: DemoDataStore | null = null;
  private isStarted = false;
  private alertsState: Alert[] = [];
  private loadPromise: Promise<DemoDataStore> | null = null;

  async load(): Promise<DemoDataStore> {
    if (this.data) return this.data;
    if (this.loadPromise) return this.loadPromise;

    this.loadPromise = (async () => {
      const res = await fetch("/data/demoData.json");
      if (!res.ok) {
        throw new Error(`Failed to load demo data: ${res.status}`);
      }
      const data = (await res.json()) as DemoDataStore;
      this.data = data;
      this.alertsState = [...data.initial.alerts];
      return data;
    })();

    return this.loadPromise;
  }

  async health(): Promise<Health> {
    const d = await this.load();
    const base = this.isStarted ? d.started.health : d.initial.health;
    return {
      status: "ok",
      scenario_hash: base.scenario_hash,
      seed: base.seed,
      demo_clock: base.demo_clock,
    };
  }

  async summary(): Promise<Summary> {
    const d = await this.load();
    return this.isStarted ? d.started.summary : d.initial.summary;
  }

  async complaints(): Promise<Complaint[]> {
    const d = await this.load();
    return this.isStarted ? d.started.complaints : d.initial.complaints;
  }

  async districts(): Promise<GeoJSON.FeatureCollection> {
    const d = await this.load();
    return d.districts;
  }

  async trace(id: string): Promise<Trace> {
    const d = await this.load();
    if (d.traces[id]) return d.traces[id];

    // Fallback to first available trace or demo case
    const fallbackId = d.demo_complaint_id;
    if (d.traces[fallbackId]) {
      const cloned = JSON.parse(JSON.stringify(d.traces[fallbackId])) as Trace;
      cloned.complaint.id = id;
      return cloned;
    }
    return Object.values(d.traces)[0] as Trace;
  }

  async account(id: string): Promise<Account> {
    const d = await this.load();
    if (d.accounts[id]) return d.accounts[id];

    // Generic fallback account
    return {
      id,
      bank: "State Bank of India",
      holder: "Simulated Account Holder",
      home_district_id: "D1",
      risk: 0.75,
      signals: [{ name: "Rapid Pass-through", reason: "Funds forwarded within 15 mins", tx_ids: [] }],
      transactions: [],
      source_transactions: [],
    };
  }

  async start(): Promise<{ complaint_id: string; demo_clock: string }> {
    const d = await this.load();
    this.isStarted = true;
    this.alertsState = [...d.started.alerts];
    return {
      complaint_id: d.demo_complaint_id,
      demo_clock: d.started.health.demo_clock || "",
    };
  }

  async reset(): Promise<{ demo_clock: string }> {
    const d = await this.load();
    this.isStarted = false;
    this.alertsState = [...d.initial.alerts];
    return {
      demo_clock: d.initial.health.demo_clock || "",
    };
  }

  async predictionCases(): Promise<PredictionCase[]> {
    const d = await this.load();
    return this.isStarted ? d.started.prediction_cases : d.initial.prediction_cases;
  }

  async predictions(id: string, model: ModelName, window: number): Promise<Prediction> {
    const d = await this.load();
    const key = `${id}_${model}_${window}`;
    if (d.predictions[key]) return d.predictions[key];

    // Try fallback to demo complaint with requested model and window
    const demoKey = `${d.demo_complaint_id}_${model}_${window}`;
    if (d.predictions[demoKey]) return d.predictions[demoKey];

    // Try any prediction for requested case
    for (const [k, p] of Object.entries(d.predictions)) {
      if (k.startsWith(id)) return p;
    }

    // Default to any available prediction
    return Object.values(d.predictions)[0] as Prediction;
  }

  async evaluation(): Promise<Evaluation> {
    const d = await this.load();
    return d.evaluation;
  }

  async alerts(): Promise<Alert[]> {
    await this.load();
    return [...this.alertsState];
  }

  async ackAlert(id: string): Promise<Alert> {
    await this.load();
    const alert = this.alertsState.find((a) => a.id === id);
    if (!alert) {
      throw new Error(`Alert ${id} not found`);
    }
    alert.status = "acknowledged";
    alert.acknowledged_at = new Date().toISOString();
    return alert;
  }

  async generateAlerts(complaintId: string): Promise<AlertGenResult> {
    const d = await this.load();
    const existing = this.alertsState.filter((a) => a.complaint_id === complaintId);
    if (existing.length > 0) {
      return {
        complaint_id: complaintId,
        new_alerts: 0,
        total_alerts: this.alertsState.length,
        message: "Alerts already generated for this case.",
      };
    }

    const newAlerts = d.started.alerts.filter((a) => a.complaint_id === complaintId);
    const alertsToAdd = newAlerts.length > 0 ? newAlerts : d.started.alerts.slice(0, 3);
    this.alertsState.push(...alertsToAdd);

    return {
      complaint_id: complaintId,
      new_alerts: alertsToAdd.length,
      total_alerts: this.alertsState.length,
      alerts: alertsToAdd,
    };
  }

  async blockRecommendations(complaintId: string): Promise<BlockRecommendation> {
    const d = await this.load();
    if (d.block_recs[complaintId]) return d.block_recs[complaintId]!;
    if (d.block_recs[d.demo_complaint_id]) return d.block_recs[d.demo_complaint_id]!;
    return Object.values(d.block_recs)[0] as BlockRecommendation;
  }

  async simulateFreeze(complaintId: string, accounts: string[]): Promise<FreezeSimulation> {
    const rec = await this.blockRecommendations(complaintId);
    const before = rec.money_reachable_before_inr || 100000;
    const frozenCount = accounts.length;
    // Each frozen node cuts a fraction of reachable flow
    const ratio = Math.min(1, frozenCount * 0.35 + (frozenCount > 0 ? 0.3 : 0));
    const prevented = Math.round(before * ratio);
    const after = before - prevented;

    return {
      accounts_frozen: accounts,
      complaint_id: complaintId,
      demo_clock: rec.demo_clock,
      money_reachable_before_inr: before,
      money_reachable_after_inr: after,
      prevented_inr: prevented,
      prevented_pct: Math.round((prevented / before) * 100) / 100,
    };
  }

  async adversaryCurves(): Promise<AdversaryCurvesResponse> {
    const d = await this.load();
    return d.curves;
  }

  async adversaryRun(complaintId?: string, hardened?: boolean): Promise<AdversaryRunResult> {
    const d = await this.load();
    const result = hardened ? d.adversary.hardened : d.adversary.baseline;
    if (complaintId) {
      return { ...result, complaint_id: complaintId };
    }
    return result;
  }
}

export const demoService = new DemoService();
