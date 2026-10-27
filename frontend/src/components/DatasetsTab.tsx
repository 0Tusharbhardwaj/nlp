import React, { useState, useEffect } from 'react';
import { Database, AlertCircle, CheckCircle } from 'lucide-react';
import type { DatasetsListResponse } from '../types/api';
import { ApiService } from '../services/api';

export const DatasetsTab: React.FC = () => {
  const [data, setData] = useState<DatasetsListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDatasets = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await ApiService.getDatasets();
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load benchmark datasets.');
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, []);

  if (loading) {
    return (
      <div className="glass-panel p-12 rounded-2xl flex flex-col items-center justify-center space-y-4">
        <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading benchmark dataset audits...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
        <p className="text-sm">{error || 'Dataset audit data unavailable.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Overview Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2">
        <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider">
          <Database className="w-4 h-4" />
          <span>Multi-Dataset Harmonization & Scope Audit</span>
        </div>
        <h2 className="text-xl font-bold text-white">Vulnerability Benchmark Datasets</h2>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          To rigorously evaluate whether models trained on human code detect AI-generated vulnerabilities,
          four primary datasets were audited. Only C/C++ function benchmarks (Devign & LLMVul) are permitted in
          training to ensure zero cross-lingual token leakage.
        </p>
      </div>

      {/* Dataset Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.datasets.map((dataset) => {
          const isExcluded = dataset.status.includes('excluded');

          return (
            <div
              key={dataset.id}
              className={`glass-panel p-6 rounded-2xl border transition-all ${
                isExcluded
                  ? 'border-amber-500/30 bg-slate-900/40 opacity-80'
                  : 'border-slate-800 hover:border-sky-500/30 shadow-sm'
              }`}
            >
              {/* Header: Title, Status, and Language Pill */}
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-white">{dataset.name}</span>
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                        dataset.language.includes('C/C++')
                          ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      }`}
                    >
                      {dataset.language}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 block">{dataset.id}</span>
                </div>

                <span
                  className={`text-[11px] font-medium px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
                    isExcluded
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  }`}
                >
                  {isExcluded ? <AlertCircle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                  <span>{isExcluded ? 'Audited & Excluded' : 'Processed & Active'}</span>
                </span>
              </div>

              {/* Provenance & Granularity */}
              <div className="my-4 space-y-2 text-xs">
                <div>
                  <strong className="text-slate-400 font-medium block">Provenance:</strong>
                  <span className="text-slate-200">{dataset.provenance}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                  <div>
                    <span className="text-slate-400 block">Granularity:</span>
                    <span className="text-slate-200 capitalize font-medium">{dataset.granularity}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Vulnerability Balance:</span>
                    <span className="text-slate-200 font-medium">
                      {dataset.vulnerability_rate ? `${dataset.vulnerability_rate.toFixed(1)}% (Balanced 1:1)` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Sample Counts Breakdown */}
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
                <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                  Processed Partitions
                </span>
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  {Object.entries(dataset.samples_count).map(([split, count]) => (
                    <div key={split} className="flex items-center gap-1.5 bg-slate-800/70 px-2.5 py-1 rounded-md">
                      <span className="text-slate-400 capitalize">{split}:</span>
                      <strong className="text-sky-300 font-mono">{count}</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Role in Pipeline */}
              <div className="mt-4 text-xs text-slate-400 border-t border-slate-800 pt-3">
                <strong className="text-slate-300 block mb-0.5">Scientific Role:</strong>
                <span>{dataset.role}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
