import { describe, expect, it } from 'vitest';
import { buildScenarioPayload, ealReduction, optimizationMetrics, remainingBudget, scenarioDefaults } from './phase6';

describe('Phase 6 decision helpers', () => {
 it('builds a numeric scenario configuration payload', () => {
  const payload = buildScenarioPayload({ ...scenarioDefaults, remediation_delay_days: '30' as never, investment_change: '100' as never });
  expect(payload.remediation_delay_days).toBe(30);
  expect(payload.investment_change).toBe(100);
  expect(payload.mfa_enabled).toBe(true);
 });
 it('calculates scenario reductions and budget remaining without negative values', () => {
  expect(ealReduction(100, 70)).toBe(30);
  expect(ealReduction(70, 100)).toBe(0);
  expect(remainingBudget(100, 120)).toBe(0);
 });
 it('derives optimization result metrics from backend output', () => {
  expect(optimizationMetrics(1000, 500, { total_cost: 350, estimated_risk_reduction: 200 })).toEqual({ remaining_budget: 150, eal_reduction: 200 });
 });
});
