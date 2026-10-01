import { PredictedAtm, Prediction, PredictionReason, Transaction, Withdrawal } from '../api/client';

export function filterAtms(atms: PredictedAtm[], thresholdPercent: number): PredictedAtm[] {
  return atms.filter(atm => atm.probability * 100 >= thresholdPercent);
}

export function sourceRecords(prediction: Prediction, atm: PredictedAtm, reason: PredictionReason): (Withdrawal | Transaction)[] {
  const source = reason.source_group;
  const history = prediction.evidence.withdrawals;
  if (source === 'past_withdrawals') return history;
  if (source === 'last_withdrawal') return history.slice(-1);
  if (source === 'atm_withdrawals') return history.filter(w => w.atm_id === atm.id);
  if (source === 'withdrawals_7d' || source === 'withdrawals_30d') {
    const days = source === 'withdrawals_7d' ? 7 : 30;
    const cutoff = new Date(prediction.prediction_time).getTime() - days * 86400000;
    return history.filter(w => w.atm_id === atm.id && new Date(w.ts).getTime() >= cutoff);
  }
  if (source === 'trace' || source === 'temporal') return prediction.evidence.transactions;
  return [];
}

export function probabilityColor(probability: number): string {
  const p = Math.max(0, Math.min(1, probability));
  return `rgb(${Math.round(76 + 179 * p)}, ${Math.round(201 - 18 * p)}, ${Math.round(240 - 237 * p)})`;
}
