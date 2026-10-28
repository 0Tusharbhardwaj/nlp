/**
 * TypeScript API contracts matching FastAPI backend schemas.
 */

export interface SystemHealth {
  status: string;
  service: string;
  environment: string;
  version: string;
  timestamp: string;
  gpu_available: boolean;
  models_ready_count: number;
  models_registered_count: number;
}

export interface ModelDetails {
  id: string;
  name: string;
  type: 'classical' | 'transformer';
  description: string;
  status: string; // 'ready', 'checkpoint_missing'
  version: string;
  training_dataset: string;
  metrics_summary?: Record<string, any>;
}

export interface ModelsListResponse {
  models: ModelDetails[];
  default_model: string;
}

export interface ScanRequest {
  code: string;
  model_id: string;
  language?: string;
  allow_fallback?: boolean;
}

export interface ScanResponse {
  model_id: string;
  model_name: string;
  model_type: string;
  requested_model?: string;
  actual_model?: string;
  fallback_used?: boolean;
  is_vulnerable: boolean;
  prediction: number;
  confidence: number;
  probabilities: {
    safe: number;
    vulnerable: number;
  };
  inference_time_ms: number;
  disclaimer: string;
}

export interface DatasetInfo {
  id: string;
  name: string;
  language: string;
  provenance: string;
  granularity: string;
  vulnerability_rate?: number;
  role: string;
  status: string;
  samples_count: Record<string, number>;
}

export interface DatasetsListResponse {
  total_datasets: number;
  datasets: DatasetInfo[];
}

export interface ExperimentResult {
  experiment_id: string;
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_negative_rate: number;
  roc_auc?: number;
  confusion_matrix: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
  };
}

export interface ExperimentItem {
  experiment_id: string;
  description: string;
  results: ExperimentResult[];
}

export interface ExperimentsListResponse {
  experiments: ExperimentItem[];
  scientific_disclaimer: string;
}
