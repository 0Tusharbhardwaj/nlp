# SecureCode AI — Security & Vulnerability Detection for LLM-Generated Code

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/Hugging%20Face-Transformers-yellow.svg)](https://huggingface.co/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite%208-61dafb.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SecureCode AI is a research-grade machine learning system designed to detect software vulnerabilities in source code. Its primary scientific focus is investigating whether vulnerability detection models trained on historical human-written code generalize to identify security flaws in AI-generated and AI-assisted code.

- **GitHub Repository**: [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)
- **Scientific Research Paper**: [docs/RESEARCH_PAPER.md](docs/RESEARCH_PAPER.md)
- **Experiment Plan**: [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md)
- **Architecture Documentation**: [docs/PROJECT_ARCHITECTURE.md](docs/PROJECT_ARCHITECTURE.md)

---

## 🎯 Research Objectives & Findings

1. **Evaluate Cross-Domain Generalization**: Determine whether fine-tuned models like Microsoft CodeBERT and classical baselines trained on human code (CodeXGLUE / Devign) can detect vulnerabilities in LLM-generated code (LLMVul).
2. **Quantify False Negative Risk**: Measure the False Negative Rate (FNR = 1 - Recall) spike when models encounter AI-generated syntactic patterns.
3. **Compare Classical Baselines vs. Transformers**: Benchmark TF-IDF + Logistic Regression and TF-IDF + Linear SVM against CodeBERT sequence classifiers.
4. **Deploy Real-World Inference**: Provide a low-latency (<15 ms), validated FastAPI backend and an interactive React + Monaco Editor scanning dashboard.

---

## 📁 Repository Layout

```text
SecureCode-AI/
├── datasets/                       # Datasets (raw, processed, external, reports)
│   ├── raw/                        # Original benchmark archives
│   ├── processed/                  # Normalized, deduplicated, split data (Devign, LLMVul, SeCodePLT)
│   └── reports/                    # Suitability, audit, and preprocessing reports
├── notebooks/                      # Colab GPU training notebooks
│   └── 01_codebert_finetuning.ipynb # Self-contained Google Colab GPU training pipeline
├── src/                            # Machine learning core package
│   ├── data/                       # Ingestion loaders & analyzer
│   ├── preprocessing/              # 5-state lexer safe comment stripper & token length audit
│   ├── models/                     # CodeBERT & classical baseline definitions
│   ├── training/                   # PyTorch training loops & checkpointing
│   ├── evaluation/                 # Metrics, FNR, visualizer, cross-evaluator
│   └── utils/                      # Hardware, config, and seed utilities
├── backend/                        # FastAPI REST API
│   └── app/
│       ├── api/                    # Route endpoints (health, scan, models, datasets, experiments)
│       ├── services/               # Model inference singleton & data services
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
├── scripts/                        # Automation & audit scripts
│   ├── verify_system.py            # End-to-end integration verification audit
│   ├── audit_datasets.py           # Dataset quality & deduplication inspector
│   ├── preprocess_data.py          # Data preprocessing pipeline runner
│   ├── train_baselines.py          # Classical baseline model trainer
│   ├── train_codebert.py           # CodeBERT training CLI
│   └── run_cross_evaluation.py     # Cross-dataset evaluation runner (E1-E4)
├── tests/                          # 39 automated unit & integration tests
├── results/                        # Models, metrics (JSON/CSV), figures (PNG), logs
└── docs/                           # Research paper, architecture, experiment plans
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

### 3. Run Test Suite

```bash
python -m unittest discover -s tests -v
# 39 unit and integration tests run across all phases
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

## 🔬 Google Colab GPU Training (CodeBERT)

For GPU acceleration and fine-tuning CodeBERT:
1. Open [`notebooks/01_codebert_finetuning.ipynb`](notebooks/01_codebert_finetuning.ipynb) in Google Colab.
2. Select **Runtime > Change runtime type > T4 GPU**.
3. Execute all cells sequentially. Checkpoints and evaluation metrics will automatically save to Google Drive and can be placed in `results/checkpoints/best_codebert.pt`.

---

## 📊 Summary of Cross-Dataset Experiments (E1–E4)

| Experiment | Training Set | Evaluation Set | Focus Metric |
| :--- | :--- | :--- | :--- |
| **E1: Human In-Distribution** | Devign Train (Human) | Devign Test (Human) | Benchmark Human Baseline |
| **E2: Zero-Shot AI Transfer** | Devign Train (Human) | LLMVul (AI Code) | Generalization Gap & FNR Spike |
| **E3: Joint Adaptation** | Devign + AI Train | LLMVul Test (Disjoint AI) | Adaptation Recovery |
| **E4: AI-Native In-Distribution** | LLMVul Train (AI Code) | LLMVul Test (Disjoint AI) | AI-Native Performance |

---

## 🗺️ Project Roadmap Status

- [x] **Phase 1**: Project Architecture, Repository Layout, Documentation & Configs.
- [x] **Phase 2**: Dataset Engineering (CodeXGLUE/Devign, LLMVul, SeCodePLT, HumanVsAICode).
- [x] **Phase 3**: Reproducible Data Preprocessing & Untruncated Token Length Audit.
- [x] **Phase 4**: Classical ML Baselines (TF-IDF + Logistic Regression, TF-IDF + Linear SVM).
- [x] **Phase 5**: CodeBERT Fine-Tuning Pipeline & Executable Google Colab GPU Notebook.
- [x] **Phase 6**: Cross-Dataset Evaluation (E1–E4), Disjoint AI Splits & FNR Spike Analysis.
- [x] **Phase 7**: Production-Grade FastAPI Backend & Inference Engine.
- [x] **Phase 8**: React 19 + TypeScript + Monaco Editor + Recharts Frontend Dashboard.
- [x] **Phase 9**: End-to-End System Integration, Launchers, Verification Audit & Dockerization.
- [x] **Phase 10**: Comprehensive Scientific Research Paper (`docs/RESEARCH_PAPER.md`).

---

## 📜 Scientific Disclaimer

This platform provides machine-learning vulnerability predictions for empirical research and defensive analysis. Outputs represent statistical estimations rather than mathematical proofs or formal verifications. It should be used in conjunction with dynamic security analysis and human code audits.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
