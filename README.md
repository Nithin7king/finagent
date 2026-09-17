# 💎 FinAgent — Multi-Agent Personal Finance Assistant

> A decentralized, multi-agent personal finance assistant combining **LangGraph orchestration**, **ML-based categorization & anomaly detection**, **Corrective RAG (CRAG)**, and local **Ollama inference** to deliver proactive, personalized financial guidance.

![Python](https://img.shields.io/badge/Python-3.10+-blue) 
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Express](https://img.shields.io/badge/Express-4.18-lightgrey)
![React](https://img.shields.io/badge/React-19-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🏗️ Architecture & Tech Stack

```
User ──▶ React Dashboard (Port 8501)
               │
               ▼
       Express.js Gateway (Port 5000)
        ├── Issues & Validates JWTs
        ├── Handles Registration & Login
        └── Proxies requests with X-User-Id
               │
               ▼
        FastAPI Backend (Port 8000)
        └── LangGraph Orchestrator (StateGraph)
             ├── 1. Monitor Agent (IsolationForest & subscription checks)
             ├── 2. Explainer Agent (Local Ollama: llama3.1)
             ├── 3. Recommender Agent (Goal/budget advice)
             └── 4. RAG Subsystem (sentence-transformers + ChromaDB)
                     └── PostgreSQL Database (alerts, recommendations, user_facts)
```

### Tech Stack Details
- **Orchestration**: **LangGraph** (`StateGraph`) — runs the Orchestrator, Monitor, Explainer, and Recommender nodes inside FastAPI.
- **Agent Host**: **FastAPI** (Python) — runs the LangGraph application; exposes endpoints for transactions, analytics, and chat.
- **Auth & Gateway**: **Express.js** (Node.js) — issues/validates JWTs, intercepts incoming requests, and routes them to FastAPI with the authenticated `X-User-Id` header. Also acts as a notification webhook receiver.
- **LLM Inference**: **Ollama** (local `llama3.1:8b` or `mistral:7b`) — powers the Explainer and Recommender nodes (Monitor runs purely on local ML for speed and cost efficiency).
- **Database**: **PostgreSQL** — handles shared persistence (users, transactions, goals, alerts, recommendations, and agent memory). Sensitive fields are encrypted at rest via AES-256-GCM.
- **Embeddings & Vector Store**: `sentence-transformers` (`all-MiniLM-L6-v2`) + ChromaDB.

---

## 🤖 Multi-Agent Roster

Unlike monolithic agent loops, FinAgent splits execution into narrow, testable roles within a LangGraph topology:

1. **Monitor Agent**: 
   - *Role*: Proactive background scanner. Runs on new transactions or every 6 hours via APScheduler.
   - *Process*: Runs scikit-learn's `IsolationForest` anomaly detector and recurring charge intervals. Runs without LLM calls for speed and zero cost.
   - *Escalation*: Writes an `AnomalyFlag` to the database. If severity is Medium or High, it triggers a conditional LangGraph edge to invoke the Explainer Agent.
2. **Explainer Agent**:
   - *Role*: Grounded anomaly descriptor.
   - *Process*: Queries the RAG subsystem and compares the transaction against user history, then prompts Ollama to explain the flag in simple language (e.g. *"This ₹4,200 charge is 4x your Electronics average"*).
3. **Recommender Agent**:
   - *Role*: Goal-oriented advisor.
   - *Process*: Reasons over current savings goals and budget status to generate advisory recommendations (e.g. *"Consider moving ₹500 to your Emergency Fund goal"*), writing them to the `recommendations` table.
4. **RAG Subsystem (with Corrective RAG)**:
   - *Role*: Shared retrieval capability.
   - *Self-Correction*: Chunks are graded by cosine similarity. If the score falls below a `0.35` threshold, the RAG engine automatically reformulates the query once and retries search before falling back.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd finagent
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` in both the project root and `gateway/` folders:
```bash
cp .env.example .env
# Also:
# Copy gateway/.env.example to gateway/.env if not handled automatically
```
Ensure your `DATABASE_URL` is pointing to your PostgreSQL instance, e.g.:
`DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finagent`

Make sure your local PostgreSQL database exists and is running.

### 3. Open-Source Local Setup (Ollama)
FinAgent runs 100% open source out of the box using **Ollama** for local inference without sending data to cloud APIs:
```bash
# 1. Download Ollama from https://ollama.com
# 2. Start local daemon
ollama serve

# 3. Pull preferred open-source model (llama3.1:8b, qwen2.5:7b, mistral, llama3.2, etc.)
ollama pull llama3.1:8b
```
Ensure `.env` contains:
```env
LLM_PROVIDER=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### 4. Run Everything

Start the unified launcher:
```bash
python run.py
```
This launcher will automatically:
1. Seed the PostgreSQL database on first run.
2. Run `npm install` inside the `gateway` folder and start the Express Gateway at **http://localhost:5000**.
3. Start the FastAPI backend on **http://localhost:8000**.
4. Start the React dashboard on **http://localhost:8501** (proxied to the Express Gateway).

---

## 🔑 Manual Setup (Step by Step)

If you prefer starting services manually in separate terminals:

```bash
# Terminal 1: Seed database
python -m backend.data.seed_data

# Terminal 1: Start FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start Express Gateway
cd gateway
npm install
node server.js

# Terminal 3: Start Frontend React Dev Server
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
│   ├── auth.py                  # Inbound X-User-Id validation
│   ├── database.py              # SQLAlchemy + PostgreSQL
│   ├── models.py                # ORM models (User, Transaction, Goal, Alert, Recommendation)
│   ├── agent/
│   │   ├── planner_langgraph.py # LangGraph Multi-Agent Orchestrator
│   │   ├── tools.py             # Transactions, forecasts, and calculations tools
│   │   └── memory.py            # Session + persistent cross-session facts
│   ├── rag/
│   │   ├── engine.py            # Self-correcting RAG pipeline + Ollama REST
│   │   └── embedder.py          # sentence-transformers + Chroma
│   └── routers/
│       ├── chat.py              # Chat routes routed through LangGraph
│       └── recommendations.py   # Recommendations CRUD endpoints
├── gateway/
│   ├── server.js                # Express.js server (JWT issuing, proxies, notification hook)
│   └── package.json             # Express dependencies
├── frontend/
│   ├── src/                     # React dashboard pages and components
│   └── vite.config.ts           # Configured to proxy /api to Express Gateway (Port 5000)
├── requirements.txt
├── run.py                       # Unified multithreaded launcher
└── README.md
```

---

## 🔒 Security & Least Privilege

- **Gateway Isolation**: Direct authentication is decoupled from the agent host; Express gateway issues JWTs and verifies all API scopes before forwarding user information to FastAPI.
- **Read-Only Agent Permissions**: Agents have no access to write to account balances or trigger money-moving endpoints.
- **AES-256 Encryption**: Sensitive transaction details are encrypted at rest in PostgreSQL. Semantically anonymized chunks are stored in ChromaDB to prevent vector store leaks.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

## 📄 License

MIT — see LICENSE file.
