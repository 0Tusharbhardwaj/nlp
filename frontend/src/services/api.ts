/**
 * SecureCode AI API Service Client.
 */

import type {
  DatasetsListResponse,
  ExperimentsListResponse,
  ModelsListResponse,
  ScanRequest,
  ScanResponse,
  SystemHealth,
} from '../types/api';

const API_BASE = '/api/v1';

export class ApiService {
  /** Fetch backend system diagnostics and health. */
  static async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      throw new Error(`Failed to check health: ${res.statusText}`);
    }
    return res.json();
  }

  /** Retrieve registered vulnerability detection models. */
  static async getModels(): Promise<ModelsListResponse> {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) {
      throw new Error(`Failed to load models: ${res.statusText}`);
    }
    return res.json();
  }

  /** Scan a single source code snippet. */
  static async scanCode(payload: ScanRequest): Promise<ScanResponse> {
    const res = await fetch(`${API_BASE}/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to scan code');
    }
    return res.json();
  }

  /** Retrieve benchmark dataset profiling details. */
  static async getDatasets(): Promise<DatasetsListResponse> {
    const res = await fetch(`${API_BASE}/datasets`);
    if (!res.ok) {
      throw new Error(`Failed to load datasets: ${res.statusText}`);
    }
    return res.json();
  }

  /** Retrieve empirical research experiment results (E1-E4). */
  static async getExperiments(): Promise<ExperimentsListResponse> {
    const res = await fetch(`${API_BASE}/experiments`);
    if (!res.ok) {
      throw new Error(`Failed to load experiments: ${res.statusText}`);
    }
    return res.json();
  }

  /** Retrieve high-level cross-dataset comparison audit. */
  static async getExperimentsComparison(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/experiments/comparison`);
    if (!res.ok) {
      throw new Error(`Failed to load comparison: ${res.statusText}`);
    }
    return res.json();
  }
}
