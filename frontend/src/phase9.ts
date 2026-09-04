export type PredictiveRisk = {
  available: boolean;
  prediction_horizon_days?: number;
  model_version?: string;
  feature_version?: string;
  feature_names?: string[];
  modelled?: boolean;
  dataset?: string;
  rows?: number;
  positive_rows?: number;
  negative_rows?: number;
  trained_at?: string;
  prediction_timestamp?: string;
  metrics?: {
    precision?: number;
    recall?: number;
    f1?: number;
    confusion_matrix?: number[][];
    evaluation_rows?: number;
  };
  target?: string;
  predicted_likelihood?: number;
  confidence?: number;
  key_predictive_drivers?: Array<{ feature?: string; value?: number; direction?: string }>;
  unavailable_reason?: string;
};

export function predictionLabel(prediction: PredictiveRisk | null | undefined): string {
  if (!prediction) return 'Prediction unavailable';
  if (!prediction.available || typeof prediction.predicted_likelihood !== 'number') return `Prediction unavailable: ${prediction.unavailable_reason || 'model data is unavailable'}`;
  return `${(prediction.predicted_likelihood * 100).toFixed(1)}% likelihood`;
}
