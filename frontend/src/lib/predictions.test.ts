import { describe, expect, it } from 'vitest';
import { PredictedAtm, Prediction, PredictionReason } from '../api/client';
import { filterAtms, probabilityColor, sourceRecords } from './predictions';

const atm = { id: 'ATM001', probability: .2 } as PredictedAtm;
const reason = (source_group: string): PredictionReason => ({ source_group, text: '', feature: null, contribution: null });
const prediction = {
  prediction_time: '2026-08-30T10:00:00+05:30',
  evidence: { transactions: [], withdrawals: [
    { id: 'old', atm_id: 'ATM001', ts: '2026-07-01T10:00:00+05:30' },
    { id: 'boundary', atm_id: 'ATM001', ts: '2026-08-23T10:00:00+05:30' },
    { id: 'recent', atm_id: 'ATM001', ts: '2026-08-29T10:00:00+05:30' },
    { id: 'other', atm_id: 'ATM002', ts: '2026-08-29T11:00:00+05:30' },
  ] },
} as unknown as Prediction;

describe('prediction controls and evidence', () => {
  it('includes threshold ties and preserves the API ranking', () => {
    const rows = [{ ...atm, probability: .8 }, atm, { ...atm, probability: .1 }];
    expect(filterAtms(rows, 20)).toEqual(rows.slice(0, 2));
    expect(filterAtms(rows, 100)).toEqual([]);
    expect(filterAtms(rows, 0)).toEqual(rows);
  });
  it('links count reasons to the correct ATM and time window', () => {
    expect(sourceRecords(prediction, atm, reason('withdrawals_7d')).map(r => r.id)).toEqual(['boundary', 'recent']);
    expect(sourceRecords(prediction, atm, reason('atm_withdrawals')).map(r => r.id)).toEqual(['old', 'boundary', 'recent']);
    expect(sourceRecords(prediction, atm, reason('last_withdrawal')).map(r => r.id)).toEqual(['other']);
  });
  it('shows all history for KDE, including non-selected ATMs', () => {
    expect(sourceRecords(prediction, atm, reason('past_withdrawals'))).toHaveLength(4);
  });
  it('bounds probability colours to the legend endpoints', () => {
    expect(probabilityColor(-1)).toBe(probabilityColor(0));
    expect(probabilityColor(2)).toBe(probabilityColor(1));
    expect(probabilityColor(.5)).not.toBe(probabilityColor(0));
  });
});
