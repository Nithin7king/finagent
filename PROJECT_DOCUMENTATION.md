# 💎 FinAgent — Comprehensive Project Documentation & Technical Specification

**Project Title:** FinAgent — Multi-Agent Personal Finance Assistant  
**Repository:** `Nithin7king/finagent`  
**System Version:** `1.0.0-MVP`  
**Document Generated:** September 22, 2026  
**Project Status:** 🟢 Active / Functional End-to-End System  

---

## 📌 1. Project Overview & Core Philosophy

**FinAgent** is an intelligent, decentralized, multi-agent personal finance assistant built to provide real-time, proactive financial advice while maintaining strict privacy and zero cloud LLM API dependence.

### Key Value Propositions
1. **100% Privacy & Local Inference:** Powered by local open-source LLMs (Ollama `llama3.1:8b` / `mistral:7b`) and local vector embeddings (`sentence-transformers`), guaranteeing user financial data never leaves the premise.
2. **Proactive Multi-Agent Topology:** Uses **LangGraph** (`StateGraph`) to partition tasks between lightweight, zero-cost ML background agents and heavy LLM reasoning agents.
3. **Corrective RAG (CRAG):** Employs self-checking retrieval that evaluates relevance confidence scores against a `0.35` cosine similarity threshold, automatically reformulating queries on low similarity before falling back.
4. **Decoupled Security Gateway:** Utilizes an Express.js security gateway for authentication and JWT management, keeping backend agent endpoints isolated from direct public authentication logic.

---

## 🏗️ 2. System Architecture & Agent Flow

```
                               ┌──────────────────────────────────────────────┐
                               │             React Web Dashboard              │
                               │          (Port 8501 - Vite / React)          │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      │ API Requests (JWT Auth)
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Express.js Security Gateway (Port 5000)                               │
│  • User Authentication & Registration (bcrypt + JWT)                                                    │
│  • Validates JWT & injects X-User-Id header                                                             │
│  • Reverse proxies requests to FastAPI Backend (Port 8000)                                              │
└─────────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                      │
                                                      │ Proxied HTTP + X-User-Id
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI Backend Engine (Port 8000)                                  │
│                                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                               LangGraph Multi-Agent Orchestrator                                  │  │
│  │                                                                                                   │  │
│  │   ┌───────────────────────────┐      Severity      ┌───────────────────────────┐                  │  │
│  │   │       Monitor Agent       │ ──Medium / High──▶ │      Explainer Agent      │                  │  │
│  │   │  (IsolationForest / ML)   │                    │      (Local Ollama)       │                  │  │
│  │   └─────────────┬─────────────┘                    └─────────────┬─────────────┘                  │  │
│  │                 │ (Severity Low/None)                            │                                │  │
│  │                 │                                                ▼                                │  │
│  │                 │                                  ┌───────────────────────────┐                  │  │
│  │                 │                                  │       RAG Subsystem       │                  │  │
│  │                 │                                  │   (ChromaDB + Sentence   │                  │  │
│  │                 │                                  │       Transformers)       │                  │  │
│  │                 │                                  └─────────────┬─────────────┘                  │  │
│  │                 │                                                │                                │  │
│  │                 ▼                                                ▼                                │  │
│  │   ┌────────────────────────────────────────────────────────────────────────┐                      │  │
│  │   │                           Recommender Agent                            │                      │  │
│  │   │          (Budget & Savings Advice; ingests Anomaly Explanations)       │                      │  │
│  │   └───────────────────────────────────┬────────────────────────────────────┘                      │  │
│  │                                       │                                                           │  │
│  │                                       ▼                                                           │  │
│  │   ┌────────────────────────────────────────────────────────────────────────┐                      │  │
│  │   │                            Synthesizer Node                            │                      │  │
│  │   │          (Compiles final user response & dispatches alerts)            │                      │  │
│  │   └────────────────────────────────────────────────────────────────────────┘                      │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                     │                                                   │
│                                                     ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                   Data & Storage Persistence                                      │  │
│  │   • PostgreSQL DB: Users, Transactions, Goals, Alerts, Recommendations, Memory Facts             │  │
│  │   • AES-256-GCM Field Encryption at Rest                                                          │  │
│  │   • ChromaDB Vector Store: Semantically anonymized document embeddings                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 3. Repository Directory Structure & Component Mapping

```
finagent/
├── backend/                             # Python FastAPI Core Application
│   ├── main.py                          # FastAPI entrypoint, lifespan events, APScheduler init
│   ├── database.py                      # SQLAlchemy engine, session management, DB Base
│   ├── models.py                        # SQLAlchemy ORM models (User, Transaction, Goal, Alert, etc.)
│   ├── schemas.py                       # Pydantic V2 request & response schemas
│   ├── auth.py                          # Inbound X-User-Id header validation & auth context
│   ├── encryption.py                    # AES-256-GCM symmetric encryption for sensitive fields
│   ├── agent/                           # Multi-Agent Framework
│   │   ├── planner_langgraph.py         # LangGraph StateGraph topology, state nodes, edges
│   │   ├── planner.py                   # Fallback agent execution pipeline
│   │   ├── tools.py                     # Financial calculation tools & database query handlers
│   │   └── memory.py                    # Long-term user fact memory extraction & storage
│   ├── ml/                              # Machine Learning Services & Training
│   │   ├── categorizer.py               # Hybrid TF-IDF + Random Forest transaction classifier (200 trees)
│   │   ├── anomaly_detector.py          # Isolation Forest anomaly detection engine
│   │   ├── forecaster.py                # Rolling 30-day avg + OLS linear trend spending forecaster
│   │   ├── subscription_detector.py     # Recurring billing interval & subscription creep scanner
│   │   └── train_all_datasets.py        # Automated ML training pipeline CLI supporting 9 local & Kaggle datasets
│   ├── rag/                             # Retrieval-Augmented Generation Subsystem
│   │   ├── engine.py                    # Corrective RAG (CRAG) pipeline with 0.35 similarity threshold & query reformulation
│   │   ├── embedder.py                  # sentence-transformers & ChromaDB vector store wrapper
│   │   └── knowledge_loader.py          # Document loader & chunk generator for knowledge base
│   └── routers/                         # REST API Route Handlers
│       ├── chat.py                      # Chat endpoint forwarding to LangGraph
│       ├── transactions.py              # Transaction management & bulk import
│       ├── analytics.py                 # Spending analytics & cash flow metrics
│       ├── goals.py                     # Financial savings goal CRUD operations
│       ├── alerts.py                    # Proactive anomaly alert endpoints
│       ├── recommendations.py          # Advisory recommendation endpoints
│       └── profile.py                   # User profile & setting routes
├── Credit Card Transactions Fraud Detection Dataset/  # Dataset 1: Daily Household Transactions
├── Credit card Fraud detection/                       # Dataset 2: Credit Card Fraud (PCA)
├── Daily Transactions Dataset/                        # Dataset 3: Personal Expense Classification
├── Indian Personal Finance and Spending Habits/       # Dataset 4: Monthly Spending Dataset (2020-2025)
├── Personal Expense Classification Dataset/           # Dataset 5: Demographic Household Expenses
├── Synthetic Financial Datasets For Fraud Detection/  # Dataset 6: Synthetic Fraud Transactions (1.29M rows)
├── gateway/                             # Express.js Authentication Gateway
├── gateway_kotlin/                      # High-Performance JVM Gateway Alternative
├── frontend/                            # React Web Application
├── frontend_flutter/                    # Cross-Platform Flutter Mobile Application
├── finagent/                            # Standalone Python / Streamlit MVP
├── run.py                               # Unified Multi-Process Orchestrated Launcher
└── requirements.txt                     # Global Python dependencies
```

---

## 📊 4. Project Datasets & Model Training Guide

The system supports **9 dataset sources** (6 local workspace dataset folders + 3 Kagglehub dataset integrations). You can download and train models across any of them using [`backend/ml/train_all_datasets.py`](file:///E:/Major%20Project/MYFY.AI/backend/ml/train_all_datasets.py):

| Dataset Source / Handle | Data File | Model Binary Output | Focus / Task | CLI Execution Command |
| :--- | :--- | :--- | :--- | :--- |
| **1. Daily Household Transactions** | `Daily Household Transactions.csv` | `household_categorizer_model.joblib` | Household transaction classifier | `python -m backend.ml.train_all_datasets --dataset household` |
| **2. Credit Card Fraud Detection** | `creditcard.csv` | `creditcard_fraud_model.joblib` | PCA feature transaction fraud detector | `python -m backend.ml.train_all_datasets --dataset cc_fraud` |
| **3. Daily Transactions Dataset** | `personal_expense_classification.csv` | `expense_classifier_model.joblib` | Merchant text description classifier | `python -m backend.ml.train_all_datasets --dataset daily_exp` |
| **4. Indian Personal Finance (2020-2025)**| `monthly_spending_dataset_2020_2025.csv` | `indian_monthly_forecaster_model.joblib` | 6-year monthly expenditure forecaster | `python -m backend.ml.train_all_datasets --dataset indian_finance` |
| **5. Personal Expense Classification** | `data.csv` | `demographic_budget_model.joblib` | Demographic income & savings predictor | `python -m backend.ml.train_all_datasets --dataset personal_expense` |
| **6. Synthetic Financial Datasets** | `fraudTrain.csv` (1.29M rows) | `synthetic_fraud_model.joblib` | Multi-feature fraud anomaly detector | `python -m backend.ml.train_all_datasets --dataset synthetic_fraud` |
| **7. Kaggle: Credit Card Habits (India)** | `thedevastator/analyzing-credit-card...` | `kaggle_indian_cc_spending_model.joblib` | Indian city & card-type spending habits model | `python -m backend.ml.train_all_datasets --dataset kaggle_cc_india` |
| **8. Kaggle: Income & Expenditure** | `saurav9786/incomeexpenditure-dataset` | `kaggle_income_expenditure_model.joblib` | Household income-to-expense regressor | `python -m backend.ml.train_all_datasets --dataset kaggle_income_exp` |
| **9. Kaggle: Monthly Expense Statewise** | `varunraskar/monthly-expense-data...` | `kaggle_statewise_expense_model.joblib` | Indian statewise monthly category forecaster | `python -m backend.ml.train_all_datasets --dataset kaggle_statewise` |

### 🚀 Train ALL 9 Datasets Simultaneously
```bash
python -m backend.ml.train_all_datasets --dataset all
```

---

## 🧮 5. Machine Learning & Algorithm Suite

FinAgent incorporates nine distinct algorithmic & machine learning models:

### 1. Transaction Categorizer (`RandomForestClassifier`) 🟢
* **File:** [`backend/ml/categorizer.py`](file:///E:/Major%20Project/MYFY.AI/backend/ml/categorizer.py)
* **Model:** `RandomForestClassifier` (200 estimators, max depth 20, min samples leaf 2, balanced class weighting).
* **Feature Engineering:** `HybridTransformer` combining TF-IDF unigrams/bigrams (`max_features=2000`) on cleaned merchant descriptions with normalized numerical features (`amount_abs`, `is_income`).
* **Fallback Strategy:** If predicted confidence score is `< 0.45`, falls back to a dictionary-based keyword matching engine (`_keyword_category`).

### 2. Anomaly Detector (`IsolationForest`) 🟢
* **File:** [`backend/ml/anomaly_detector.py`](file:///E:/Major%20Project/MYFY.AI/backend/ml/anomaly_detector.py)
* **Model:** `IsolationForest` (100 estimators, 5% contamination factor).
* **Feature Set:** Transaction amount, category encoding, and time-of-day / day-of-week distribution.
* **Scoring & Severity:** Calculates z-score anomaly strength against historical category baseline:
  - Severity `low`: Anomaly score $< 0.4$
  - Severity `medium`: Anomaly score $0.4 \le s < 0.75$
  - Severity `high`: Anomaly score $\ge 0.75$ (Triggers conditional LangGraph execution).

### 3. Spending Forecaster (Rolling Avg + OLS Linear Trend) 🟢
* **File:** [`backend/ml/forecaster.py`](file:///E:/Major%20Project/MYFY.AI/backend/ml/forecaster.py)
* **Method:** Rolling 30-day daily spending average combined with Ordinary Least Squares (OLS) linear trend extrapolation (`np.polyfit(x, y, 1)`).
* **Blending:** 70% trend-adjusted projection + 30% rolling average projection over a 90-day lookback window.
* **Horizon & Metrics:** Generates 30, 60, or 90 day forecasts for total expenses, category-wise breakdown, projected income, and predicted net savings rate.

### 4. Subscription & Recurring-Charge Detector 🟢
* **File:** [`backend/ml/subscription_detector.py`](file:///E:/Major%20Project/MYFY.AI/backend/ml/subscription_detector.py)
* **Method:** Merchant normalization key grouping + amount-variance tolerance (`amount_cv <= 0.15`).
* **Interval Analysis:** Evaluates charge interval regularity against candidate cycles (7, 14, 28, 30, 31 days) within a $\pm 4$ day window ($std \le 5$ days).
* **Subscription Creep Score:** Computes total monthly recurring cost as a percentage of monthly income:
  - **Healthy:** $\le 5\%$ of income
  - **Moderate:** $5\% - 10\%$ of income
  - **High Risk:** $> 10\%$ of income (triggers audit alert).

### 5. Corrective RAG (CRAG) with Self-Correction 🟢
* **Files:** [`backend/rag/engine.py`](file:///E:/Major%20Project/MYFY.AI/backend/rag/engine.py), [`backend/rag/embedder.py`](file:///E:/Major%20Project/MYFY.AI/backend/rag/embedder.py)
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
* **Vector Store:** ChromaDB (`chroma_db/`).
* **Self-Correction Logic:** Cosine similarity threshold `RELEVANCE_THRESHOLD = 0.35`. If retrieved chunks score below 0.35, CRAG invokes an LLM query optimizer to reformulate the user query and re-searches ChromaDB once before falling back to non-retrieval mode.

### 6. Local LLM Reasoning Engine (Ollama) 🟢
* **Files:** [`backend/rag/engine.py`](file:///E:/Major%20Project/MYFY.AI/backend/rag/engine.py), [`backend/agent/planner_langgraph.py`](file:///E:/Major%20Project/MYFY.AI/backend/agent/planner_langgraph.py)
* **Model:** Local Ollama runtime (`llama3.1:8b` or `mistral:7b`) accessed via REST API (`http://localhost:11434/api/generate`). Zero external API token cost.

---

## 🔒 6. Security Architecture & Encryption Specs

FinAgent implements a 4-layer defense-in-depth security model:

| Layer | Feature | Technology / Library | Implementation File |
| :--- | :--- | :--- | :--- |
| **Authentication** | Password Hashing | `bcrypt` (10 rounds) | [`gateway/server.js`](file:///E:/Major%20Project/MYFY.AI/gateway/server.js) |
| **Session Security** | JWT Signing & Verification | `jsonwebtoken` (HS256) | [`gateway/server.js`](file:///E:/Major%20Project/MYFY.AI/gateway/server.js) |
| **Backend Auth Validation**| Inbound Header Verification | `X-User-Id` validation | [`backend/auth.py`](file:///E:/Major%20Project/MYFY.AI/backend/auth.py) |
| **Data Encryption at Rest** | Field-Level Encryption | AES-256-GCM | [`backend/encryption.py`](file:///E:/Major%20Project/MYFY.AI/backend/encryption.py) |
| **Agent Least Privilege** | Access Control Scoping | Read-only transactions, write-only alerts/recs | [`backend/agent/planner_langgraph.py`](file:///E:/Major%20Project/MYFY.AI/backend/agent/planner_langgraph.py) |

---

## 💻 7. Software & Hardware Requirements

### Software Requirements
* **Runtime & Languages:** Python 3.10+, Node.js 18.x+, Dart 3.x / Flutter 3.x, Kotlin 1.9+ (JVM 17).
* **Backend Frameworks:** FastAPI 0.111, Uvicorn, APScheduler 3.10, SQLAlchemy 2.0, Pydantic V2.
* **Security & Gateway:** Express.js 4.18, `jsonwebtoken` 9.0, `bcryptjs` 2.4, `cors`.
* **Database & Vector Store:** PostgreSQL 15+, ChromaDB 0.4+, `sentence-transformers` 2.5+.
* **Machine Learning & Kaggle:** `scikit-learn` 1.4, `joblib` 1.3, `pandas` 2.2, `numpy` 1.26, `kagglehub`.
* **Agent Orchestration:** `langgraph` 0.1+, `langchain` 0.1+.
* **Local LLM Runtime:** Ollama local daemon (`llama3.1:8b` / `mistral:7b`).
* **Frontend Web:** React 19, Vite 5, Tailwind CSS.

### Hardware Requirements
* **CPU:** Quad-Core 2.5 GHz x86_64 / ARM64 processor (Intel i5/i7, AMD Ryzen 5/7, or Apple Silicon M1/M2/M3).
* **RAM:** Minimum 8 GB RAM (16 GB RAM recommended for running local Ollama 8B parameter models smoothly).
* **Storage:** 10 GB free SSD disk space (models + PostgreSQL + ChromaDB store).

---

## 🚦 8. Detailed Project Status & Component Matrix

| Subsystem / Module | Technology | Completion Status | Notes |
| :--- | :--- | :---: | :--- |
| **FastAPI Core Backend** | Python 3.10+, FastAPI | 🟢 **100% Complete** | Fully functional REST routes, auth middleware, DB integrations |
| **LangGraph Agent Engine** | LangGraph, LangChain | 🟢 **100% Complete** | State graph execution with memory persistence and tools |
| **ML Engine & Models** | Scikit-learn, Joblib | 🟢 **100% Complete** | Categorizer, Anomaly Detector, Forecaster, Subscription Detector |
| **Corrective RAG Pipeline** | ChromaDB, SentenceTransformers | 🟢 **100% Complete** | Vector search with 0.35 threshold & self-correcting query reformulation |
| **Express Security Gateway**| Node.js, Express.js | 🟢 **100% Complete** | JWT auth, password hashing, API proxying operational |
| **React Web Dashboard** | React 19, Vite, Tailwind | 🟢 **100% Complete** | Responsive web UI running on port 8501 |
| **Standalone Streamlit MVP**| Python, Streamlit | 🟢 **100% Complete** | Independent testbench app (`finagent/app.py`) fully working |
| **Unified Multi-Launcher** | Python (`run.py`) | 🟢 **100% Complete** | Automatic process management and database auto-seeding |
| **Flutter Mobile Client** | Dart, Flutter | 🟡 **60% Active Dev** | Screens and models designed; API service integration in progress |
| **Kotlin Gateway Service** | Kotlin, Gradle, JVM | 🟡 **50% In Progress** | Core setup complete; router porting ongoing |

---

## 🛠️ 9. Quick Start & Execution Guide

### Option A: One-Command Unified Launcher (Recommended)
```bash
python run.py
```
This launcher automatically:
1. Validates local environment files (`.env`).
2. Seeds PostgreSQL on first run (creates `.db_seeded`).
3. Runs `npm install` in `gateway/` and starts Express Gateway at **http://localhost:5000**.
4. Starts FastAPI backend on **http://localhost:8000**.
5. Boots React dashboard on **http://localhost:8501**.

### Option B: Manual Terminal Execution

```bash
# Terminal 1: Database Seed & FastAPI Backend
python -m backend.data.seed_data
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Express Gateway
cd gateway
npm install
node server.js

# Terminal 3: React Dashboard
cd frontend
npm install
npm run dev

# Terminal 4: Ollama LLM Service
ollama serve
ollama pull llama3.1:8b
```

---

## 📌 10. Service Port & Endpoint Summary

| Service | Protocol | Host / Port | Target / Role |
| :--- | :--- | :--- | :--- |
| **Express Gateway** | HTTP / REST | `http://localhost:5000` | Primary API entrypoint for web/mobile clients |
| **FastAPI Backend** | HTTP / REST | `http://localhost:8000` | Internal backend service proxied by Gateway |
| **React Web Dashboard** | HTTP / Web | `http://localhost:8501` | Front-end web dashboard UI |
| **Standalone Streamlit**| HTTP / Web | `http://localhost:8501` | Alternate offline Streamlit test app |
| **Ollama Inference** | HTTP / REST | `http://localhost:11434`| Local LLM inference server |
| **PostgreSQL Database** | TCP / SQL | `localhost:5432` | Relational database (`finagent`) |

---

## 🚀 11. Future Scope & Roadmap

1. 📱 **Flutter Mobile Client Completion:** Finalize mobile client UI state providers and bind to Express Gateway (`:5000`) for Android/iOS releases (~60% complete).
2. ⚡ **Kotlin JVM Gateway Migration:** Complete endpoint router migration for high-performance JVM gateway alternative in [`gateway_kotlin/`](file:///E:/Major%20Project/MYFY.AI/gateway_kotlin) (~50% complete).
3. 🧪 **Automated E2E Test Suite:** Implement comprehensive pytest suite covering LangGraph state transitions, CRAG query reformulations, and fallback paths.
