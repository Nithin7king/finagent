"""
agent.py
The FinAgent orchestrator. Implements a plan -> act -> observe -> respond loop
that decides which tools to call (ML models, RAG, calculator, alerts) based on
the user's question - instead of following one fixed script.

NOTE: This uses rule/keyword-based intent routing to stay fully offline and free
to run. In production, swap `route_intent()` for an LLM function-calling call
(e.g. the Claude API) so routing is handled by the model instead of keywords -
the rest of the tool architecture (tools, self-check, state) stays the same.
"""

import datetime
import pandas as pd
from ml_models import CategorizationModel, AnomalyDetector, forecast_next_month, detect_subscriptions
from rag import KnowledgeRetriever, TransactionRetriever, self_check_relevance


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------

def tool_calculate(expression):
    """Safe-ish calculator tool for interest/loan/savings math."""
    try:
        allowed = "0123456789+-*/.() "
        if not all(c in allowed for c in expression):
            return "Error: invalid characters in expression."
        return eval(expression, {"__builtins__": {}})
    except Exception as e:
        return f"Error: {e}"


def tool_loan_payoff_savings(principal, old_rate, new_rate, years):
    """Rough estimate of interest saved by refinancing (simple interest approximation)."""
    old_interest = principal * (old_rate / 100) * years
    new_interest = principal * (new_rate / 100) * years
    return round(old_interest - new_interest, 2)


# ---------------------------------------------------------------------------
# STATE (so the agent doesn't repeat the same alert - simple in-memory store)
# ---------------------------------------------------------------------------

class AgentState:
    def __init__(self):
        self.sent_alerts = set()
        self.goals = {}  # {goal_name: {"target": amount, "by": date, "saved": amount}}

    def already_alerted(self, alert_key):
        return alert_key in self.sent_alerts

    def mark_alerted(self, alert_key):
        self.sent_alerts.add(alert_key)

    def set_goal(self, name, target, by_date):
        self.goals[name] = {"target": target, "by": by_date, "saved": 0.0}

    def update_goal_progress(self, name, saved_amount):
        if name in self.goals:
            self.goals[name]["saved"] = saved_amount


# ---------------------------------------------------------------------------
# INTENT ROUTER (stand-in for LLM function-calling)
# ---------------------------------------------------------------------------

def route_intent(query):
    q = query.lower()
    if any(k in q for k in ["refinance", "should i pay off", "payoff", "interest saved"]):
        return "loan_decision"
    if any(k in q for k in ["forecast", "predict", "next month", "will i spend"]):
        return "forecast"
    if any(k in q for k in ["anomaly", "fraud", "unusual", "suspicious"]):
        return "anomaly"
    if any(k in q for k in ["subscription", "recurring"]):
        return "subscriptions"
    if any(k in q for k in ["tax", "80c", "budget rule", "50/30/20", "emergency fund"]):
        return "knowledge"
    if any(k in q for k in ["spend", "spent", "how much"]):
        return "transaction_query"
    return "general_rag"


# ---------------------------------------------------------------------------
# AGENT
# ---------------------------------------------------------------------------

class FinAgent:
    def __init__(self, transactions_df):
        self.df = transactions_df
        self.state = AgentState()

        # initialize ML models
        self.cat_model = CategorizationModel().fit(self.df)
        self.anomaly_model = AnomalyDetector().fit(self.df)

        # initialize RAG retrievers
        self.kb_retriever = KnowledgeRetriever()
        self.txn_retriever = TransactionRetriever(self.df)

    # -- individual tool-backed capabilities -----------------------------
    def answer_transaction_query(self, query):
        results = self.txn_retriever.retrieve(query, top_k=10)
        if results.empty:
            results = self.txn_retriever.filter_by_category_keyword(query)
        if results.empty:
            return "I couldn't find matching transactions for that query.", results
        total = results["amount"].sum()
        answer = f"Found {len(results)} matching transactions totaling ₹{total:,.2f}."
        return answer, results

    def answer_knowledge_query(self, query):
        chunks = self.kb_retriever.retrieve(query, top_k=2)
        ok, check_msg = self_check_relevance(query, chunks, min_score=0.03)
        if not ok:
            return f"I don't have grounded information to answer that confidently. ({check_msg})", []
        combined = " ".join(c["text"] for c in chunks)
        answer = f"Based on retrieved guidance: {combined[:400]}..."
        return answer, chunks

    def answer_forecast_query(self, query):
        forecasts = forecast_next_month(self.df)
        lines = [f"{cat}: ₹{amt:,.2f}" for cat, amt in sorted(forecasts.items(), key=lambda x: -x[1])]
        answer = "Forecasted next month spend by category:\n" + "\n".join(lines[:6])
        return answer, forecasts

    def answer_anomaly_query(self):
        results = self.anomaly_model.detect(self.df)
        flagged = results[results["is_anomaly"]]
        merged = flagged.merge(self.df, on="transaction_id")
        answer = f"Found {len(flagged)} anomalous transactions out of {len(self.df)}."
        return answer, merged[["transaction_id", "date", "merchant", "category", "amount", "explanation"]]

    def answer_subscription_query(self):
        subs = detect_subscriptions(self.df)
        subs = subs[subs["category"] != "Income"]
        answer = f"Found {len(subs)} recurring subscription-like charges."
        return answer, subs

    def answer_loan_decision(self, query, principal=500000, old_rate=11.0, new_rate=9.0, years=3):
        """Multi-step reasoning: RAG (grounding) + calculator (math) combined."""
        kb_chunks = self.kb_retriever.retrieve("loan refinancing", top_k=1)
        ok, _ = self_check_relevance(query, kb_chunks, min_score=0.03)
        grounding = kb_chunks[0]["text"] if ok else "General refinancing guidance unavailable."

        savings = tool_loan_payoff_savings(principal, old_rate, new_rate, years)
        recommendation = "refinancing looks worthwhile" if savings > 0 else "refinancing may not be worth it"

        answer = (
            f"Estimated interest saved over {years} years by moving from {old_rate}% to {new_rate}%: "
            f"₹{savings:,.2f}. Based on general guidance, {recommendation}.\n\n"
            f"Grounding context: {grounding[:250]}..."
        )
        return answer, {"savings": savings, "grounding": grounding}

    # -- main entry point: plan -> act -> observe -> respond ---------------
    def ask(self, query):
        intent = route_intent(query)  # PLAN: decide which tool path to use

        if intent == "transaction_query":
            answer, data = self.answer_transaction_query(query)      # ACT
        elif intent == "knowledge":
            answer, data = self.answer_knowledge_query(query)
        elif intent == "forecast":
            answer, data = self.answer_forecast_query(query)
        elif intent == "anomaly":
            answer, data = self.answer_anomaly_query()
        elif intent == "subscriptions":
            answer, data = self.answer_subscription_query()
        elif intent == "loan_decision":
            answer, data = self.answer_loan_decision(query)
        else:
            answer, data = self.answer_knowledge_query(query)        # fallback: general RAG

        return {"intent": intent, "answer": answer, "data": data}    # RESPOND

    # -- proactive / scheduled monitoring (the "agentic" part) -------------
    def run_scheduled_check(self):
        """
        Simulates the weekly digest / monitoring agent: checks for anomalies
        and subscription creep, and only 'alerts' on things not already flagged
        (state-tracked, so it doesn't repeat itself).
        """
        alerts = []

        anomaly_results = self.anomaly_model.detect(self.df)
        flagged = anomaly_results[anomaly_results["is_anomaly"]]
        for _, row in flagged.iterrows():
            key = f"anomaly:{row['transaction_id']}"
            if not self.state.already_alerted(key):
                alerts.append(f"[ANOMALY] {row['transaction_id']}: {row['explanation']}")
                self.state.mark_alerted(key)

        subs = detect_subscriptions(self.df)
        subs = subs[subs["category"] != "Income"]
        for _, row in subs.iterrows():
            key = f"subscription:{row['merchant']}"
            if not self.state.already_alerted(key):
                alerts.append(
                    f"[SUBSCRIPTION] {row['merchant']} charges ~₹{row['avg_amount']:.0f} "
                    f"({row['occurrences']} times) - review if still needed."
                )
                self.state.mark_alerted(key)

        return alerts


if __name__ == "__main__":
    from data_gen import generate_transactions, inject_anomalies

    df = generate_transactions(500, seed=42)
    df = inject_anomalies(df, n_anomalies=8, seed=7)

    agent = FinAgent(df)

    test_queries = [
        "How much did I spend on dining?",
        "Should I refinance my loan?",
        "What will I spend next month?",
        "Any unusual transactions?",
        "What subscriptions do I have?",
        "What is the 50/30/20 budgeting rule?",
    ]

    for q in test_queries:
        print(f"\nQ: {q}")
        result = agent.ask(q)
        print(f"[intent: {result['intent']}]")
        print(result["answer"])

    print("\n\n=== Scheduled proactive check (run 1) ===")
    alerts = agent.run_scheduled_check()
    for a in alerts[:5]:
        print(a)
    print(f"...({len(alerts)} total alerts)")

    print("\n=== Scheduled proactive check (run 2, should NOT repeat same alerts) ===")
    alerts2 = agent.run_scheduled_check()
    print(f"New alerts this run: {len(alerts2)} (should be 0 since nothing changed)")
