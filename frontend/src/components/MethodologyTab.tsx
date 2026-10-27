import React from 'react';
import { Layers, ShieldCheck, Binary, Cpu, Network, CheckCircle2, AlertOctagon, Terminal } from 'lucide-react';

export const MethodologyTab: React.FC = () => {
  const steps = [
    {
      phase: 'Phase 1–2',
      title: 'Dataset Engineering & Harmonization',
      icon: <Network className="w-5 h-5 text-sky-400" />,
      description:
        'Unified schema across CodeXGLUE/Devign, LLMVul, SeCodePLT, and HumanVsAICode. Audited exact/near duplicate leakage and strictly isolated C/C++ function benchmarks from Python/Java snippets.',
    },
    {
      phase: 'Phase 3',
      title: 'Syntax-Aware Preprocessing Pipeline',
      icon: <Terminal className="w-5 h-5 text-emerald-400" />,
      description:
        'A deterministic 5-state lexer safely strips single-line and multi-line comments without damaging URL slashes or string literal quotes. Preserved untruncated AST tokens for 512-length audit.',
    },
    {
      phase: 'Phase 4',
      title: 'Classical Machine Learning Baselines',
      icon: <Binary className="w-5 h-5 text-indigo-400" />,
      description:
        'Fitted TF-IDF n-gram vectorizers (1-2 grams with operator tokens) strictly on human training sets. Built balanced Logistic Regression and Linear SVM with sigmoid Platt scaling.',
    },
    {
      phase: 'Phase 5',
      title: 'CodeBERT Contextual Fine-Tuning',
      icon: <Cpu className="w-5 h-5 text-purple-400" />,
      description:
        'Built a 2-class classification head atop microsoft/codebert-base (12 layers, 768 hidden, 12 heads). Generated fully self-contained Colab GPU training notebook with checkpoint resumption.',
    },
    {
      phase: 'Phase 6',
      title: 'Repository-Disjoint Cross-Evaluation',
      icon: <AlertOctagon className="w-5 h-5 text-rose-400" />,
      description:
        'Partitioned AI code strictly by repository ID to eliminate test leakage. Benchmarked E1 (Human In-Dist), E2 (Zero-Shot AI Transfer), E3 (Joint Adaptation), and tracked False Negative Rate (FNR) spikes.',
    },
    {
      phase: 'Phase 7–8',
      title: 'FastAPI Serving & Interactive Dashboard',
      icon: <ShieldCheck className="w-5 h-5 text-teal-400" />,
      description:
        'Low-latency REST API with lifespan model caching, input validation, and Monaco Editor UI enabling interactive vulnerability scanning with confidence meters and disclaimers.',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Overview Card */}
      <div className="glass-panel p-6 lg:p-8 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider">
          <Layers className="w-4 h-4" />
          <span>Scientific Methodology & Architecture</span>
        </div>
        <h2 className="text-xl lg:text-2xl font-bold text-white tracking-tight">
          Research Architecture & Experimental Pipeline
        </h2>
        <p className="text-sm text-slate-300 max-w-4xl leading-relaxed">
          SecureCode AI explores the vulnerability detection frontier between human-authored code and LLM-generated code.
          Our empirical protocol enforces strict data hygiene, preventing data snooping, vectorizer leakage, and repository overlap.
        </p>
      </div>

      {/* Pipeline Steps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {steps.map((step, idx) => (
          <div key={idx} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
                  {step.phase}
                </span>
                <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700">
                  {step.icon}
                </div>
              </div>

              <h4 className="text-base font-bold text-white">{step.title}</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{step.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center gap-1.5 text-[11px] text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verified & Audited</span>
            </div>
          </div>
        ))}
      </div>

      {/* Core Security Metrics Formula Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white">Mathematical Security Formulations</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase text-[10px] block">False Negative Rate (FNR)</span>
            <div className="text-rose-400 font-bold text-sm">FNR = FN / (TP + FN)</div>
            <p className="text-[11px] text-slate-400 font-sans mt-1">Percentage of actual security vulnerabilities missed by the model.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase text-[10px] block">Recall / Sensitivity</span>
            <div className="text-emerald-400 font-bold text-sm">Recall = TP / (TP + FN)</div>
            <p className="text-[11px] text-slate-400 font-sans mt-1">Proportion of vulnerable samples accurately detected (Recall = 1 - FNR).</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase text-[10px] block">Platt Scaling Sigmoid</span>
            <div className="text-sky-400 font-bold text-sm">P(y=1) = 1 / (1 + e^-w^T x)</div>
            <p className="text-[11px] text-slate-400 font-sans mt-1">Calibrates Linear SVM hyperplane distances into smooth probabilities.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
