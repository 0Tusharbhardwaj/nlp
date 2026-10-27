# SecureCode AI — Security & Vulnerability Detection for LLM-Generated Code

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/Hugging%20Face-Transformers-yellow.svg)](https://huggingface.co/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61dafb.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SecureCode AI is a reproducible, research-grade machine learning system designed to detect software vulnerabilities in source code. Its primary scientific focus is evaluating whether vulnerability detection models trained on historical human-written code can generalize to identify security flaws in AI-generated and AI-assisted source code.

---

## 🎯 Research Objectives

1. **Evaluate Cross-Domain Generalization**: Determine whether fine-tuned models like Microsoft CodeBERT trained on human code (CodeXGLUE / Devign) can detect vulnerabilities in LLM-generated code (LLMVul).
2. **Quantify False Negative Risk**: Measure the False Negative Rate (FNR) spike when models encounter AI-generated syntactic patterns.
3. **Compare Classical Baselines vs. Transformers**: Benchmark TF-IDF + Logistic Regression and TF-IDF + Linear SVM against CodeBERT sequence classifiers.
4. **Deploy Real-World Inference**: Provide a low-latency, validated FastAPI backend and an interactive React + Monaco Editor scanning dashboard.

For detailed experiment designs, see [docs/EXPERIMENT_PLAN.md](file:///docs/EXPERIMENT_PLAN.md).  
For the complete system architecture, see [docs/PROJECT_ARCHITECTURE.md](file:///docs/PROJECT_ARCHITECTURE.md).

---

## 📁 Project Architecture

```text
SecureCode-AI/
├── datasets/                       # Datasets (raw, processed, external, reports)
│   ├── raw/                        # Original benchmark archives
│   ├── processed/                  # Normalized, deduplicated, split data
│   ├── external/                   # External evaluation benchmarks (LLMVul)
│   └── reports/                    # Dataset profiling and schema audits
├── notebooks/                      # Colab GPU training notebooks
├── src/                            # Machine learning core package
│   ├── data/                       # Ingestion scripts & loaders
│   ├── preprocessing/              # Tokenization, safe cleaning, deduplication
│   ├── models/                     # CodeBERT & classical baseline definitions
│   ├── training/                   # PyTorch training loops & checkpointing
│   ├── evaluation/                 # Metrics, FNR, and confusion matrices
│   ├── inference/                  # Prediction engine for production serving
│   └── utils/                      # Config loaders, seeds, hardware utils
├── backend/                        # FastAPI REST API
│   └── app/
│       ├── api/                    # API route endpoints
│       ├── services/               # Model inference service orchestrators
│       ├── schemas/                # Pydantic validation schemas
│       ├── core/                   # App settings & CORS configuration
│       └── main.py                 # FastAPI application entry point
├── frontend/                       # React + TypeScript + Monaco Editor interface
├── configs/                        # YAML configuration files
│   └── base.yaml                   # Central project & training hyperparameters
├── scripts/                        # Reproducible automation scripts
├── tests/                          # Automated Pytest suite
├── results/                        # Outputs (checkpoints, metrics, figures)
└── docs/                           # Architecture and experiment plans
```

---

## 🛠️ Technology Stack

- **Machine Learning**: Python 3.11, PyTorch, Hugging Face Transformers (`microsoft/codebert-base`), Datasets, Scikit-learn, Pandas, NumPy.
- **Training Acceleration**: Google Colab NVIDIA T4/V100/A100 GPU with Google Drive checkpoint storage.
- **Backend API**: FastAPI, Pydantic v2, Uvicorn.
- **Frontend Dashboard**: React, TypeScript, Tailwind CSS, Monaco Editor, Recharts.
- **Experiment Management & Rigor**: PyYAML, deterministic seeding (`seed=42`), MinHash near-duplicate filtering.

---

## 🚀 Setup & Installation

### Option 1: Local Development Setup (Python 3.11)

1. **Clone or navigate to the workspace**:
   ```bash
   cd "c:/Users/tusha/OneDrive/Desktop/sem 5/nlp"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

5. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

6. **Start the FastAPI backend server**:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   API interactive documentation will be accessible at: `http://localhost:8000/docs`.

---

### Option 2: Google Colab GPU Setup (For Model Training)

CodeBERT fine-tuning is performed on Google Colab GPU to leverage NVIDIA tensor cores:

1. **Open Google Colab** and select a GPU runtime (`Runtime > Change runtime type > T4 GPU`).
2. **Mount Google Drive** to persist dataset caches and model weights:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
3. **Clone or upload project files**:
   ```bash
   !git clone <YOUR_REPO_URL> /content/SecureCode-AI
   %cd /content/SecureCode-AI
   ```
4. **Install requirements**:
   ```bash
   !pip install -r requirements.txt
   ```
5. **Open and run the training notebook**:
   Open `notebooks/01_codebert_finetuning.ipynb` and execute cells sequentially.
6. Checkpoints and evaluation metrics will save directly to `/content/drive/MyDrive/SecureCode-AI/checkpoints/`.

---

## 🔬 Scientific Integrity & Non-Fabrication Rules

- **Zero Synthetic Metrics**: Metrics reported in dashboards, tables, and papers reflect genuine evaluation runs over verified dataset splits.
- **Strict Leakage Prevention**: Training, validation, and test sets are strictly isolated before feature extraction and tokenization. Cross-split near-duplicate checking is enforced.
- **Realistic Output**: The scanner outputs probabilistic vulnerability estimates and confidence levels, explicitly noting model limitations without fabricating nonexistent vulnerability lines or fake CWE classifications.

---

## 🗺️ Project Roadmap

- [x] **Phase 1**: Project Architecture, Repository Layout, Documentation & Configs.
- [ ] **Phase 2**: Dataset Engineering (CodeXGLUE/Devign, LLMVul, SECODEPLT, HumanVsAICode).
- [ ] **Phase 3**: Reproducible Data Preprocessing & Deduplication Pipeline.
- [ ] **Phase 4**: Classical ML Baselines (TF-IDF + Logistic Regression, TF-IDF + Linear SVM).
- [ ] **Phase 5**: CodeBERT Fine-Tuning on Google Colab GPU.
- [ ] **Phase 6**: Cross-Dataset Evaluation (E1–E4) & False Negative Rate Analysis.
- [ ] **Phase 7**: Production-Grade FastAPI Backend & Inference Engine.
- [ ] **Phase 8**: React + TypeScript + Monaco Editor Frontend Dashboard.
- [ ] **Phase 9 & 10**: Integration Testing, Verification Audit & Research Reporting.
