import { describe, expect, it } from 'vitest';
import { predictionLabel } from './phase9';

describe('phase 9 predictive risk helpers', () => {
  it('formats an available modelled likelihood', () => {
    expect(predictionLabel({ available: true, prediction_horizon_days: 90, model_version: 'v1', predicted_likelihood: 0.42 })).toBe('42.0% likelihood');
  });

  it('explains unavailable model output', () => {
    expect(predictionLabel({ available: false, prediction_horizon_days: 90, model_version: 'v1', unavailable_reason: 'single_target_class' })).toContain('single_target_class');
    expect(predictionLabel(null)).toBe('Prediction unavailable');
  });
});
