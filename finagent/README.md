# FinAgent — AI-Powered Personal Finance Assistant

An MVP demonstrating **ML + RAG + Agentic AI** working together for personal finance
management. Fully offline/free to run — no bank API, no paid LLM API required.

## What's inside

| File | Purpose |
|---|---|
| `data_gen.py` | Generates synthetic bank transactions (simulates a live feed) |
| `ml_models.py` | Categorization, anomaly detection, forecasting, subscription detection |
| `rag.py` | TF-IDF based retrieval over transactions + financial knowledge docs, with a self-check (Corrective RAG) step |
| `agent.py` | The orchestrator — routes queries to tools, chains multi-step reasoning, runs proactive scheduled checks with alert-dedup state |
| `app.py` | Streamlit UI — chat, dashboard, alerts, what-if simulator |
| `knowledge_base/` | Sample budgeting + tax reference docs used for grounded RAG answers |

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

This opens a browser UI with four tabs: **Chat**, **Dashboard**, **Alerts**, and **What-If**.

## How to test the core logic without the UI

Each module has a runnable demo at the bottom:

```bash
python3 data_gen.py     # generates and prints sample transactions
python3 ml_models.py    # tests categorization, anomaly detection, forecasting
python3 rag.py          # tests retrieval over transactions + knowledge base
python3 agent.py        # tests the full agent: multi-step reasoning + proactive alerts
```

## Architecture (what maps to what)

- **ML layer**: `CategorizationModel` (TF-IDF + Logistic Regression), `AnomalyDetector`
  (Isolation Forest + z-score explanation), `forecast_next_month()` (weighted moving
  average), `detect_subscriptions()` (recurring-charge detection)
- **RAG layer**: `KnowledgeRetriever` (static docs: tax rules, budgeting frameworks),
  `TransactionRetriever` (your own transaction history), `self_check_relevance()`
  (Corrective RAG — rejects weak retrieval instead of letting the LLM guess)
- **Agent layer**: `FinAgent.ask()` implements plan → act → observe → respond;
  `route_intent()` decides which tool to call; `run_scheduled_check()` is the
  proactive monitoring agent with dedup state (`AgentState`) so it never repeats
  the same alert

## Notes on what's simplified for offline/free operation

- **Intent routing** uses keyword matching (`route_intent()`) instead of an LLM
  function-calling call. In production, swap this for a Claude API call with tool
  definitions — the rest of the architecture (tools, self-check, state) stays the same.
- **Embeddings** use TF-IDF instead of a neural embedding model, since this runs
  fully offline with no external API. Swap in `sentence-transformers` or an LLM
  embedding API for stronger semantic retrieval.
- **Bank data** is synthetic (via `data_gen.py`), since free live bank API access
  isn't available in India for individual developers (Plaid doesn't support India;
  Account Aggregator sandboxes like Setu/Finvu require business registration).
  Swap in a CSV-upload of real statements or an Account Aggregator integration
  for production use.

## Security notes (for report/demo — not fully implemented in this MVP)

The architecture is designed to support: AES-256 encryption at rest for sensitive
fields, JWT-based authentication, tokenized bank credentials (never storing raw
bank passwords), and restricting the agent to read/alert-only permissions (no
ability to move money). These weren't wired into this offline MVP since it has
no real accounts/auth layer, but are documented in the project report as the
production security design.
