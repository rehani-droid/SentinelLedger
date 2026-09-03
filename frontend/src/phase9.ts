export type PredictiveRisk = {
  available: boolean;
  prediction_horizon_days: number;
  model_version: string;
  predicted_likelihood?: number;
  unavailable_reason?: string;
};

export function predictionLabel(prediction: PredictiveRisk | null | undefined): string {
  if (!prediction) return 'Prediction unavailable';
  if (!prediction.available) return `Prediction unavailable: ${prediction.unavailable_reason || 'model data is unavailable'}`;
  return `${(prediction.predicted_likelihood! * 100).toFixed(1)}% likelihood`;
}
