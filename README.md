# 💎 FinAgent — AI-Powered Personal Finance Assistant

> Combining **ML-based categorization & anomaly detection**, **RAG-grounded Q&A**, and an **autonomous multi-step agent** for proactive, personalized financial guidance.

![Python](https://img.shields.io/badge/Python-3.10+-blue) 
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![React](https://img.shields.io/badge/React-19-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🏗️ Architecture

```
User → React Dashboard
         │
         ▼
    FastAPI Backend
         │
    ├── Auth (JWT + bcrypt)
    ├── AI Agent (plan → act → observe → respond)
    │    ├── ML Engine (sklearn)
    │    │    ├── RandomForest Categorizer + SHAP
    │    │    ├── IsolationForest Anomaly Detector
    │    │    ├── Linear Trend Forecaster
    │    │    └── Subscription Detector
    │    ├── RAG Engine (Chroma + Gemini)
    │    │    ├── Self-correcting retrieval pipeline
    │    │    └── Knowledge Base (Tax, Budgeting, Investing)
    │    └── 6 Agent Tools
    ├── APScheduler (weekly digest, bill reminders, anomaly scan)
    └── PostgreSQL DB (AES-256 encrypted sensitive fields)
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd finagent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (or leave blank for offline mode)
# Ensure you configure your PostgreSQL connection string in DATABASE_URL
```

Make sure your PostgreSQL server is running and the database (default `finagent`) has been created.

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Run Everything

```bash
python run.py
```

This will:
- Seed the database with a demo user + 12 months of synthetic transactions
- Start FastAPI backend at **http://localhost:8000**
- Start React frontend at **http://localhost:8501**

### 4. Login

Open **http://localhost:8501** and use the demo credentials:
- **Email:** `demo@finagent.ai`
- **Password:** `Demo@123`

Or click **"Try Demo"** for instant access.

---

## 🔑 Manual Setup (Step by Step)

```bash
# Terminal 1: Seed database
python -m backend.data.seed_data

# Terminal 1: Start backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Install and start frontend
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
finagent/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── auth.py                  # JWT + bcrypt authentication
│   ├── database.py              # SQLAlchemy + PostgreSQL
│   ├── models.py                # ORM models (User, Transaction, Goal, Alert, Memory)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── encryption.py            # AES-256-GCM field encryption
│   ├── ml/
│   │   ├── categorizer.py       # RandomForest + TF-IDF, SHAP explanations
│   │   ├── anomaly_detector.py  # IsolationForest with rule-based explanations
│   │   ├── forecaster.py        # Rolling mean + linear trend forecasting
│   │   └── subscription_detector.py  # Recurring charge detection
│   ├── rag/
│   │   ├── embedder.py          # sentence-transformers + Chroma
│   │   ├── knowledge_loader.py  # Chunk & embed knowledge base docs
│   │   └── engine.py            # Self-correcting RAG pipeline
│   ├── agent/
│   │   ├── tools.py             # 6 agent tools (get_transactions, anomalies, etc.)
│   │   ├── memory.py            # Session + cross-session memory
│   │   └── planner.py           # Autonomous plan→act→observe→respond loop
│   ├── routers/
│   │   ├── transactions.py      # CRUD + CSV upload
│   │   ├── analytics.py         # ML insights endpoints
│   │   ├── chat.py              # Agent chat endpoint
│   │   └── goals.py             # Savings goals CRUD
│   ├── scheduler/
│   │   └── jobs.py              # APScheduler: digest, reminders, scan
│   └── data/
│       ├── synthetic_generator.py   # Realistic Indian transaction generator
│       ├── seed_data.py             # DB seeder
│       └── knowledge_base/          # Tax rules, budgeting, investing docs
├── frontend/
│   ├── src/                     # React pages, components, and API adapter
│   ├── package.json             # Frontend scripts and dependencies
│   └── vite.config.ts           # Dev server and FastAPI proxy
├── requirements.txt
├── .env.example
├── run.py                       # Unified launcher
└── README.md
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| Passwords | bcrypt with cost=12 |
| Authentication | JWT (HS256, 24-hour expiry) |
| Sensitive fields | AES-256-GCM encryption at rest |
| Data isolation | Row-level user_id filtering on ALL queries |
| Agent permissions | Read-only (cannot move money or modify critical settings) |
| SQL injection | SQLAlchemy ORM with parameterized queries |
| Transport | CORS-configured for frontend origin only |

---

## 🤖 ML/AI Components

### 1. Transaction Categorizer
- **Model:** RandomForestClassifier (200 trees)
- **Features:** TF-IDF on merchant name (bigrams) + amount + income flag
- **Categories:** 11 categories (Food, Transport, Shopping, Utilities, Healthcare, Entertainment, Income, Investments, Education, Travel, Other)
- **Fallback:** Keyword matching when confidence < 45%
- **Explainability:** Confidence score + matched keywords

### 2. Anomaly Detector  
- **Model:** IsolationForest (200 estimators, 5% contamination)
- **Features:** Amount, log-amount, day of week, hour, is_weekend
- **Explanation:** Rule-based SHAP-style — compares against per-category historical statistics
- **Severity:** Low (< 0.50) / Medium (0.50–0.75) / High (> 0.75)

### 3. Spending Forecaster
- **Method:** Rolling 30-day mean + linear OLS trend extrapolation
- **Horizons:** 7, 14, 30, 60, 90 days
- **Blend:** 70% trend-based + 30% rolling average
- **Per-category:** Separate forecast for each spending category

### 4. Subscription Detector
- **Method:** Amount tolerance grouping (±10%) + interval regularity (±4 days)
- **Intervals:** Weekly, biweekly, monthly detection
- **Output:** Monthly cost, creep score, next charge prediction

### 5. RAG Engine
- **Embeddings:** `all-MiniLM-L6-v2` (sentence-transformers)
- **Vector DB:** ChromaDB (persistent)
- **Self-correction:** Cosine similarity grading (threshold: 0.35)
- **Knowledge base:** Indian tax rules, 50/30/20 budgeting, investing, emergency fund

### 6. Autonomous Agent
- **Architecture:** Custom plan → act → observe → respond loop
- **Tools:** get_transactions, get_anomalies, forecast_spending, check_goal, calculate, search_knowledge
- **Memory:** Session (last 10 turns) + cross-session persistent facts
- **LLM:** Gemini 1.5 Flash (or Anthropic Claude, configurable via .env)

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/auth/register` | POST | Register user |
| `/auth/login` | POST | Login, get JWT |
| `/auth/me` | GET | Current user profile |
| `/transactions` | GET/POST | List/create transactions |
| `/transactions/upload-csv` | POST | Upload CSV with auto-categorization |
| `/analytics/summary` | GET | Spending summary by category |
| `/analytics/forecast` | GET | 30/60/90-day spending forecast |
| `/analytics/anomalies` | GET | Flagged anomalous transactions |
| `/analytics/subscriptions` | GET | Detected subscriptions + creep score |
| `/analytics/what-if` | GET | What-if spending simulator |
| `/analytics/train-models` | POST | Train ML models on user data |
| `/chat` | POST | Agent chat endpoint |
| `/chat/digest` | GET | Weekly financial digest |
| `/goals` | GET/POST | List/create savings goals |
| `/goals/{id}/contribute` | POST | Add contribution to goal |

Full interactive docs: **http://localhost:8000/docs**

---

## 🛠️ Configuration

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | AES-256 encryption key (32 chars) | (required) |
| `JWT_SECRET` | JWT signing key | (required) |
| `LLM_PROVIDER` | `gemini` / `anthropic` / `offline` | `gemini` |
| `GEMINI_API_KEY` | Google AI Studio API key | (required for AI) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/finagent` |
| `CHROMA_PERSIST_DIR` | Chroma vector DB directory | `./chroma_db` |

---

## 🧪 Testing

```bash
# Verify database seeding
python -m backend.data.seed_data

# Test ML components
python -c "from backend.ml.categorizer import get_categorizer; c = get_categorizer(); print(c.predict('Zomato', -350))"

# Test synthetic data generation
python -m backend.data.synthetic_generator

# API health check
curl http://localhost:8000/health
```

---

## 📈 What Makes FinAgent Unique

Unlike projects that bolt ML, RAG, and agents together as separate demos, FinAgent uses them as **one interdependent pipeline**:

1. **ML output shapes RAG retrieval** — anomaly score and category influence what context the RAG fetches
2. **RAG output feeds agent calculations** — retrieved tax rules + spending data enable grounded recommendations
3. **Agent runs proactively** — not just when prompted, but via scheduled jobs every 6 hours
4. **Memory is persistent** — the agent remembers your income, goals, and past conversations

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

## 📄 License

MIT — see LICENSE file.
