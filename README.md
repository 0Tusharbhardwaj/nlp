# SecureCode AI — Neural Vulnerability Detection & Cross-Domain Evaluation

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/Hugging%20Face-Transformers-yellow.svg)](https://huggingface.co/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite%208-61dafb.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SecureCode AI is a research-grade machine learning system designed for **static source code vulnerability detection** at the function level (C/C++). Its primary scientific focus is investigating the **Domain Generalization Gap**: whether deep neural vulnerability detectors trained exclusively on historical human-written codebases (such as CodeXGLUE / Devign) generalize to source code authored by frontier Large Language Models (LLMs).

- **GitHub Repository**: [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)
- **Scientific Research Paper**: [docs/RESEARCH_PAPER.md](docs/RESEARCH_PAPER.md)
- **LaTeX / Overleaf Template**: [docs/paper/main.tex](docs/paper/main.tex) & [docs/paper/references.bib](docs/paper/references.bib)
- **Implementation & Deliverable Plan**: [docs/FINAL_RESEARCH_PAPER_PLAN.md](docs/FINAL_RESEARCH_PAPER_PLAN.md)
- **Architecture Documentation**: [docs/PROJECT_ARCHITECTURE.md](docs/PROJECT_ARCHITECTURE.md)

---

## 🎯 Scope Boundary & Core Empirical Findings

In accordance with rigorous academic and industrial practice, this project explicitly focuses on **static, function-level binary vulnerability classification** (e.g., CWE-120 buffer overflow, CWE-78 command injection, CWE-415 double free) rather than claiming full-system security assurance.

### Verified Full-Scale Benchmark Matrix

All metrics are grounded in empirical evaluations across **51,000+ C functions**:

| Setting | Model | Evaluation Cohort ($N$) | Accuracy | Precision | Recall | Macro F1 | FNR ($1 - \text{Recall}$) | ROC-AUC |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline 1** | TF-IDF + Logistic Reg. | Devign Test ($2,732$) | 61.35% | 57.23% | 62.79% | 61.30% | 37.21% | 0.6734 |
| **Baseline 2** | TF-IDF + Linear SVM | Devign Test ($2,732$) | 59.44% | 56.93% | 48.13% | 58.48% | 51.87% | 0.6634 |
| **E1 (In-Dist)** | **Microsoft CodeBERT** | **Devign Test ($2,732$)** | **66.36%** | **68.96%** | **48.69%** | **64.71%** | **51.31%** | **0.7301** |
| **E2 (AI Transfer)** | **Microsoft CodeBERT** | **LLMVul Holdout ($4,120$)** | **8.93%** | **8.84%** | **100.0%** | **8.23%** | **0.00%** | **0.6888** |
| **Gold Standard** | Microsoft CodeBERT | Expert AI Gold ($85$) | 97.65% | 97.65\% | 100.0% | 49.40% | 0.00% | 0.3675 |
| **CVE Transfer** | Microsoft CodeBERT | SeCodePLT Pairs ($2,480$) | 50.00% | 50.00% | 99.84% | 33.48% | 0.16% | 0.4993 |

### Key Scientific Takeaways
1. **Domain Collapse ($\Delta \text{Macro F1} = -56.48\%$):** Deploying human-trained CodeBERT zero-shot on LLM-generated code causes a severe performance collapse ($64.71\% \rightarrow 8.23\%$) due to a massive false-positive surge triggered by stylistic distribution shift.
2. **Surgical Patch Blindness (50.00% Accuracy on SeCodePLT):** Function-level sequence classification cannot distinguish subtle 1–3 line CVE vulnerability fixes from vulnerable code (ROC-AUC 0.4993 = coin toss).
3. **Benchmark Memorization:** The official Devign test split shares 100% of its repositories (`qemu`, `ffmpeg`) with the training split, indicating that benchmark metrics in literature are partially inflated by repository memorization.

---

## 📁 Repository Layout

```text
SecureCode-AI/
├── datasets/                       # Datasets (raw, processed, external, reports)
│   ├── raw/                        # Original benchmark archives
│   ├── processed/                  # Normalized, deduplicated, split data (Devign, LLMVul, SeCodePLT)
│   └── reports/                    # Suitability, audit, and preprocessing reports
├── notebooks/                      # Colab GPU reproducible research notebooks
│   ├── 02_full_scale_baselines.ipynb       # TF-IDF + Logistic Reg / Linear SVM tuning on 27,318 samples
│   ├── 03_codebert_full_scale_training.ipynb # 3-epoch CodeBERT fine-tuning pipeline with checkpoints
│   └── 04_cross_dataset_evaluation.ipynb   # Cross-dataset benchmark matrix generation (E1–E4)
├── src/                            # Machine learning core package
│   ├── data/                       # Ingestion loaders & 0%-leakage greedy repository partitioner
│   ├── preprocessing/              # Deterministic 5-state lexer safe comment stripper
│   ├── models/                     # CodeBERT & calibrated classical baseline definitions
│   ├── training/                   # PyTorch training loops & checkpointing
│   ├── evaluation/                 # Metrics, FNR, visualizer, cross-evaluator
│   └── utils/                      # Hardware, config, and seed utilities
├── backend/                        # FastAPI REST API
│   └── app/
│       ├── api/                    # Route endpoints (health, scan, models, datasets, experiments)
│       ├── services/               # Model inference singleton & multi-model dispatch
│       ├── schemas/                # Pydantic validation schemas
│       ├── core/                   # App settings & CORS configuration
│       └── main.py                 # FastAPI application entry point
├── frontend/                       # React 19 + TypeScript + Monaco Editor interface
│   ├── src/
│   │   ├── components/             # Scanner, Experiments, Datasets, Methodology, Header, Footer
│   │   ├── services/               # API client
│   │   └── types/                  # TypeScript API contracts
│   └── tailwind.config.js          # Tailwind CSS v3 theme configuration
├── configs/                        # YAML configuration files (base.yaml, preprocessing.yaml)
├── docker/                         # Dockerfiles for backend, frontend & Nginx config
├── docker-compose.yml              # Multi-container orchestration
├── run_app.py                      # One-command cross-platform launcher (Backend + Frontend)
├── run_app.bat                     # Windows one-click launcher
├── run_app.sh                      # Linux/macOS one-click launcher
├── scripts/                        # Automation & verification scripts
│   ├── verify_system.py            # End-to-end integration verification audit
│   ├── audit_datasets.py           # Dataset quality & deduplication inspector
│   ├── preprocess_data.py          # Data preprocessing pipeline runner
│   ├── train_baselines.py          # Classical baseline model trainer
│   ├── train_codebert.py           # CodeBERT training CLI
│   └── run_cross_evaluation.py     # Cross-dataset evaluation runner
├── tests/                          # 44 automated unit & integration tests
├── results/                        # Models, metrics (JSON/CSV), figures (PNG), logs
│   ├── models/                     # Full-scale production models & CodeBERT weights
│   └── metrics/                    # Verified full-scale empirical JSON evaluations
└── docs/                           # Research paper, Overleaf LaTeX template, architecture
    ├── RESEARCH_PAPER.md           # Complete scientific paper draft
    ├── FINAL_RESEARCH_PAPER_PLAN.md # Comprehensive deliverables and milestones plan
    ├── PROJECT_ARCHITECTURE.md     # Architectural specification
    └── paper/                      # Overleaf / IEEEtran LaTeX paper template
        ├── main.tex                # Submission-ready IEEEtran document
        └── references.bib          # BibTeX references
```

---

## ⚡ Quick Start: Running the Full Application

### 1. Launch with One Command (Backend + Frontend)

```bash
# Cross-platform (Windows / Linux / macOS)
python run_app.py

# Or on Windows:
run_app.bat

# Or on Linux / macOS:
chmod +x run_app.sh && ./run_app.sh
```

- **Interactive Web Dashboard**: `http://localhost:5173`
- **FastAPI Interactive Docs**: `http://localhost:8000/docs`
- **Health & Telemetry**: `http://localhost:8000/api/v1/health`

---

### 2. End-to-End System Verification Audit

Run the automated integration audit to verify checkpoints, processed datasets, API responses, inference latencies, and frontend assets:

```bash
python scripts/verify_system.py
```

### 3. Run Complete Test Suite

```bash
python -m unittest discover -s tests -v
# 44 unit and integration tests run across all components
```

---

## 🐳 Docker Deployment

To launch SecureCode AI in production containers using Docker Compose:

```bash
# Build and start both Backend and Frontend containers
docker-compose up --build -d

# View status
docker-compose ps
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`

---

## 🔬 Google Colab GPU Reproducibility

For full-scale GPU replication:
1. Open [`notebooks/03_codebert_full_scale_training.ipynb`](notebooks/03_codebert_full_scale_training.ipynb) in Google Colab.
2. Select **Runtime > Change runtime type > T4 GPU**.
3. Execute all cells sequentially. Checkpoints and evaluation metrics will automatically save to Google Drive and can be downloaded into `results/models/codebert_devign_full/`.

---

## 📜 Scientific Disclaimer

This platform provides machine-learning vulnerability predictions for empirical research and defensive analysis. Outputs represent statistical estimations rather than mathematical proofs or formal verifications. It should be used in conjunction with dynamic security analysis and human code audits.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
