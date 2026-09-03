import { describe, expect, it } from 'vitest';
import { assistantExamples, formatIntent } from './phase8';

describe('phase 8 assistant helpers', () => {
  it('provides concise supported examples', () => {
    expect(assistantExamples.length).toBeGreaterThanOrEqual(4);
    expect(assistantExamples.some((item) => item.includes('MFA'))).toBe(true);
  });

  it('formats routed intent names for presentation', () => {
    expect(formatIntent('budget_optimization')).toBe('Budget Optimization');
  });
});
