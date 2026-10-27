import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  BarChart3,
  AlertTriangle,
  Info,
  TrendingUp,
  GitBranch,
} from 'lucide-react';
import type { ExperimentsListResponse } from '../types/api';
import { ApiService } from '../services/api';

export const ExperimentsTab: React.FC = () => {
  const [data, setData] = useState<ExperimentsListResponse | null>(null);
  const [comparison, setComparison] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExperimentData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [expRes, compRes] = await Promise.all([
          ApiService.getExperiments(),
          ApiService.getExperimentsComparison(),
        ]);
        setData(expRes);
        setComparison(compRes);
      } catch (err: any) {
        setError(err.message || 'Failed to load experimental evaluations.');
      } finally {
        setLoading(false);
      }
    };
    fetchExperimentData();
  }, []);

  if (loading) {
    return (
      <div className="glass-panel p-12 rounded-2xl flex flex-col items-center justify-center space-y-4">
        <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading empirical cross-dataset benchmarks...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-2">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span>Error Loading Benchmarks</span>
        </div>
        <p className="text-sm">{error || 'No experiment data available.'}</p>
      </div>
    );
  }

  // Format Recharts data across experiments for Logistic Regression and Linear SVM
  const chartData = data.experiments.flatMap((exp) => {
    return exp.results.map((res) => ({
      name: `${exp.experiment_id.split('_')[0]}: ${res.model_name}`,
      experiment: exp.experiment_id,
      model: res.model_name,
      accuracy: Number((res.accuracy * 100).toFixed(1)),
      recall: Number((res.recall * 100).toFixed(1)),
      f1_score: Number((res.f1_score * 100).toFixed(1)),
      fnr: Number((res.false_negative_rate * 100).toFixed(1)),
    }));
  });

  return (
    <div className="space-y-8">
      {/* Research Thesis Hero Card */}
      <div className="glass-panel p-6 lg:p-8 rounded-2xl border border-sky-500/20 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-3">
          <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider">
            <TrendingUp className="w-4 h-4" />
            <span>Core Scientific Thesis & Generalization Audit</span>
          </div>
          <h2 className="text-xl lg:text-2xl font-bold text-white tracking-tight">
            Cross-Dataset Generalization & False Negative Rate (FNR) Spike
          </h2>
          <p className="text-sm text-slate-300 max-w-4xl leading-relaxed">
            {comparison?.thesis || (
              <>
                In binary vulnerability detection, models trained purely on human code (such as{' '}
                <strong className="text-sky-300">CodeXGLUE / Devign</strong>) encounter systematic domain shift when evaluated
                on AI-generated code (<strong className="text-sky-300">LLMVul</strong>). While accuracy or precision may appear
                deceptively stable, the critical metric is{' '}
                <strong className="text-rose-400">False Negative Rate (FNR = 1 - Recall)</strong>: every missed vulnerability
                represents an undetected security flaw deployed into production.
              </>
            )}
          </p>
        </div>
      </div>

      {/* Recharts Visualization Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-sky-400" />
              <span>Model Performance Across Empirical Splits (E1–E3)</span>
            </h3>
            <p className="text-xs text-slate-400">
              Comparative metrics across Human In-Distribution, Zero-Shot AI Transfer, and Joint Adaptation.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-sm bg-sky-500 inline-block" /> Accuracy
            <span className="w-3 h-3 rounded-sm bg-emerald-500 inline-block ml-2" /> Recall
            <span className="w-3 h-3 rounded-sm bg-rose-500 inline-block ml-2" /> FNR (Missed Bugs)
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} angle={-15} textAnchor="end" />
              <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: '#f8fafc',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              <Bar dataKey="accuracy" name="Accuracy (%)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="recall" name="Recall (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="f1_score" name="F1 Score (%)" fill="#818cf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="fnr" name="False Negative Rate (%)" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid of Experiment Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.experiments.map((exp) => (
          <div key={exp.experiment_id} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  {exp.experiment_id}
                </span>
                <h4 className="text-base font-bold text-white mt-1">
                  {exp.experiment_id.replace(/_/g, ' ')}
                </h4>
              </div>
              <GitBranch className="w-5 h-5 text-slate-500 shrink-0" />
            </div>

            <p className="text-xs text-slate-300 leading-relaxed min-h-[38px]">{exp.description}</p>

            {/* Results table for this experiment */}
            {exp.results.length > 0 ? (
              <div className="space-y-3">
                {exp.results.map((res) => (
                  <div key={res.model_name} className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-slate-200">{res.model_name}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          res.false_negative_rate > 0.0
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}
                      >
                        FNR: {(res.false_negative_rate * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-1.5 rounded bg-slate-800/60">
                        <span className="text-[10px] text-slate-400 block">Accuracy</span>
                        <strong className="text-sky-300">{(res.accuracy * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-800/60">
                        <span className="text-[10px] text-slate-400 block">Precision</span>
                        <strong className="text-slate-200">{(res.precision * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-800/60">
                        <span className="text-[10px] text-slate-400 block">Recall</span>
                        <strong className="text-emerald-300">{(res.recall * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-800/60">
                        <span className="text-[10px] text-slate-400 block">F1 Score</span>
                        <strong className="text-indigo-300">{(res.f1_score * 100).toFixed(1)}%</strong>
                      </div>
                    </div>

                    {/* Mini Confusion Matrix Pill */}
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                      <span>Confusion Matrix:</span>
                      <span className="font-mono text-slate-300">
                        TN: {res.confusion_matrix.tn} | FP: {res.confusion_matrix.fp} | FN: {res.confusion_matrix.fn} | TP: {res.confusion_matrix.tp}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400 italic text-center">
                Experiment holdout skipped: insufficient class diversity in AI training split.
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Regulatory & Scientific Disclaimer */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-xs text-slate-400 flex items-start gap-3">
        <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">{data.scientific_disclaimer}</p>
      </div>
    </div>
  );
};
