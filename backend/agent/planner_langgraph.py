"""
FinAgent — Multi-Agent Orchestrator via LangGraph
Defines StateGraph, nodes, conditional edges, and execution triggers.
"""
import os
import json
import uuid
import pandas as pd
import requests as http_requests
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Optional, Any, Literal
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from backend import models
from backend.agent.memory import AgentMemory
from backend.agent.tools import get_transactions, get_anomalies, forecast_spending, get_subscriptions
from backend.rag.engine import get_rag_engine, _call_llm
from backend.rag.knowledge_loader import retrieve
from backend.ml.anomaly_detector import get_detector
from backend.ml.subscription_detector import get_subscription_detector

# ─── State Definition ─────────────────────────────────────────────────────────

class Message(TypedDict):
    role: str
    content: str


class AnomalyFlag(TypedDict):
    id: Optional[int]
    transaction_id: Optional[int]
    description: str
    amount: float
    category: str
    severity: str        # low | medium | high
    anomaly_score: float
    explanation: Optional[str]


class RecommendationItem(TypedDict):
    title: str
    message: str
    priority: str        # low | medium | high
    is_actioned: bool


class FinAgentState(TypedDict):
    user_id: int
    session_id: str
    user_message: str
    history: List[Message]
    user_facts: List[str]
    
    # Roster data
    anomaly_flags: List[AnomalyFlag]
    retrieved_context: str
    explanation: Optional[str]
    recommendations: List[RecommendationItem]
    final_response: str
    
    # Controlling logic
    trigger: Literal["user_message", "scheduled_scan", "new_transaction"]
    severity_reached: Literal["none", "low", "medium", "high"]


# ─── Agent Node Actions ──────────────────────────────────────────────────────

def retriever_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Context & Knowledge Retriever Agent
    Detects user intent and retrieves exact ground-truth financial data:
    - Active subscriptions & recurring charges
    - Category spending & transaction records
    - Overall monthly financial summary & savings rate
    - Savings goals & budget leeway
    - Chroma vector RAG knowledge for conceptual questions
    """
    user_id = state["user_id"]
    user_msg = state.get("user_message", "").lower()
    
    context_parts = []
    
    # 1. Intent: Subscriptions & Recurring Bills
    if any(kw in user_msg for kw in ["subscri", "recurring", "bill", "membership", "netflix", "prime", "spotify", "hotstar", "jio", "airtel", "plan", "active sub", "emi"]):
        try:
            subs_data = get_subscriptions(db, user_id)
            subs = subs_data.get("subscriptions", [])
            if subs:
                total_m = subs_data.get("total_monthly", sum(s["monthly_cost"] for s in subs))
                lines = [f"### Active Subscriptions & Recurring Bills ({len(subs)} detected, Total: ₹{total_m:,.2f}/month):"]
                for s in subs:
                    next_date = s["next_expected"].strftime("%b %d, %Y") if hasattr(s.get("next_expected"), "strftime") else str(s.get("next_expected", "N/A"))
                    lines.append(f"- **{s['merchant']}**: ₹{s['amount']:,.2f} (every {s.get('interval_days', 30)} days, approx ₹{s.get('monthly_cost', s['amount']):,.2f}/month) | Next expected charge: {next_date}")
                context_parts.append("\n".join(lines))
            else:
                context_parts.append("### Active Subscriptions:\nNo active recurring subscriptions or auto-debit services were detected in your transaction history (last 180 days).")
        except Exception as e:
            print(f"[Retriever Node] Error fetching subscriptions: {e}")
            
    # 2. Intent: Category Spending (Food, Shopping, Travel, etc.)
    categories_to_check = {
        "food": "Food & Dining",
        "dining": "Food & Dining",
        "restaurant": "Food & Dining",
        "zomato": "Food & Dining",
        "swiggy": "Food & Dining",
        "grocer": "Food & Dining",
        "blinkit": "Food & Dining",
        "transport": "Transport",
        "travel": "Travel",
        "uber": "Transport",
        "ola": "Transport",
        "shopping": "Shopping",
        "amazon": "Shopping",
        "flipkart": "Shopping",
        "myntra": "Shopping",
        "entertainment": "Entertainment",
        "movie": "Entertainment",
        "health": "Healthcare",
        "medical": "Healthcare",
        "utility": "Utilities & Bills",
        "utilities": "Utilities & Bills",
        "bills": "Utilities & Bills",
        "education": "Education",
        "invest": "Investments"
    }
    
    matched_cat = None
    for kw, cat in categories_to_check.items():
        if kw in user_msg:
            matched_cat = cat
            break
            
    if matched_cat:
        try:
            cat_txns = (
                db.query(models.Transaction)
                .filter(
                    models.Transaction.user_id == user_id,
                    models.Transaction.amount < 0,
                    models.Transaction.category.ilike(f"%{matched_cat}%")
                )
                .order_by(models.Transaction.date.desc())
                .limit(15)
                .all()
            )
            total_cat = sum(abs(t.amount) for t in cat_txns)
            lines = [f"### Category Spend: {matched_cat}"]
            lines.append(f"- Total Recorded Spend in {matched_cat}: ₹{total_cat:,.2f} across {len(cat_txns)} recent transactions")
            if cat_txns:
                lines.append("- Recent Transactions:")
                for t in cat_txns[:6]:
                    d_str = t.date.strftime("%b %d, %Y") if hasattr(t.date, "strftime") else str(t.date)
                    lines.append(f"  * {d_str}: {t.description} - ₹{abs(t.amount):,.2f}")
            context_parts.append("\n".join(lines))
        except Exception as e:
            print(f"[Retriever Node] Error fetching category spending: {e}")
        
    # 3. Intent: Overall Spending / Expense Summary / Income / Balance
    if any(kw in user_msg for kw in ["summary", "recent expense", "recent transaction", "how much did i spend", "total spend", "my expense", "overview", "statement", "income", "balance", "spending", "passbook"]):
        try:
            txn_summary = get_transactions(db, user_id, days=30)
            if "error" not in txn_summary:
                lines = ["### Financial Overview (Last 30 Days):"]
                lines.append(f"- Total Income: ₹{txn_summary.get('total_income', 0):,.2f}")
                lines.append(f"- Total Expenses: ₹{txn_summary.get('total_expenses', 0):,.2f}")
                lines.append(f"- Net Savings: ₹{txn_summary.get('net_savings', 0):,.2f} (Savings Rate: {txn_summary.get('savings_rate', 0)}%)")
                lines.append(f"- Total Transactions: {txn_summary.get('transaction_count', 0)}")
                top_cats = txn_summary.get("by_category", {})
                if top_cats:
                    lines.append("- Category Breakdown: " + ", ".join(f"{k}: ₹{v:,.0f}" for k, v in list(top_cats.items())[:5]))
                top_txns = txn_summary.get("top_expenses", [])
                if top_txns:
                    lines.append("- Top Expenses: " + ", ".join(f"{t['description']} ({t['amount']})" for t in top_txns[:3]))
                context_parts.append("\n".join(lines))
        except Exception as e:
            print(f"[Retriever Node] Error fetching transaction summary: {e}")
            
    # 4. Intent: Savings advice / Goals / "How can I save ₹X"
    if any(kw in user_msg for kw in ["save", "saving", "goal", "target", "budget", "cut back", "emergency fund", "how can i save"]):
        try:
            goals = db.query(models.Goal).filter(models.Goal.user_id == user_id, models.Goal.is_completed == False).all()
            lines = ["### Savings Goals & Budget Assessment:"]
            if goals:
                lines.append("Active Goals:")
                for g in goals:
                    rem = max(0, g.target_amount - g.current_amount)
                    lines.append(f"- **{g.name}**: Target ₹{g.target_amount:,.0f}, Saved ₹{g.current_amount:,.0f} (Remaining: ₹{rem:,.0f})")
            else:
                lines.append("- No active savings goals configured yet.")
                
            txn_summary = get_transactions(db, user_id, days=30)
            by_cat = txn_summary.get("by_category", {})
            discretionary_total = sum(by_cat.get(c, 0) for c in ["Food & Dining", "Shopping", "Entertainment"])
            lines.append(f"- Monthly Discretionary Outflow (Dining + Shopping + Entertainment): ₹{discretionary_total:,.2f}")
            context_parts.append("\n".join(lines))
        except Exception as e:
            print(f"[Retriever Node] Error fetching goals: {e}")
        
    # 5. Intent: Tax / Guidelines / Knowledge Base RAG
    if any(kw in user_msg for kw in ["tax", "80c", "80d", "regime", "nps", "deduction", "sip", "mutual fund", "index", "50/30/20", "emergency fund"]):
        try:
            chunks = retrieve(state["user_message"], n_results=2)
            if chunks:
                relevant = [c[0] for c in chunks if c[2] >= 0.35]
                if relevant:
                    context_parts.append("### Verified Financial Knowledge:\n" + "\n\n".join(relevant))
        except Exception as e:
            print(f"[Retriever Node] RAG retrieval error: {e}")

    # Fallback: if nothing specific was matched, include a baseline 30-day summary so agent always has user context
    if not context_parts:
        try:
            txn_summary = get_transactions(db, user_id, days=30)
            if "error" not in txn_summary:
                context_parts.append(
                    f"### Account Summary (Last 30 Days):\n"
                    f"- Income: ₹{txn_summary.get('total_income', 0):,.2f}, Expenses: ₹{txn_summary.get('total_expenses', 0):,.2f}, "
                    f"Savings: ₹{txn_summary.get('net_savings', 0):,.2f} ({txn_summary.get('savings_rate', 0)}% rate)"
                )
        except Exception:
            pass
            
    return {
        "retrieved_context": "\n\n".join(context_parts)
    }


def monitor_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Monitor Agent (Deterministic ML scorer + subscription check)
    Runs without LLM call. Generates alerts.
    """
    user_id = state["user_id"]
    print(f"[Monitor Node] Running continuous checks for user_id={user_id}")
    
    # 1. Fetch transactions from the last 7 days (with fallback to recent transactions)
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.date >= datetime.utcnow() - timedelta(days=7)
        )
        .all()
    )
    if not txns:
        txns = (
            db.query(models.Transaction)
            .filter(models.Transaction.user_id == user_id)
            .order_by(models.Transaction.date.desc())
            .limit(20)
            .all()
        )
    
    # 2. Score anomalies using IsolationForest
    detector = get_detector()
    anomaly_flags = []
    max_severity = "none"
    
    # Run fit if needed or score directly
    for t in txns:
        if t.amount < 0: # Only score expenses
            try:
                score, severity, explanation = detector.score_transaction(
                    amount=t.amount,
                    date=t.date,
                    category=t.category,
                    description=t.description
                )
                
                # Check if it was already flagged to avoid alert spamming
                existing_alert = db.query(models.Alert).filter(
                    models.Alert.user_id == user_id,
                    models.Alert.transaction_id == t.id
                ).first()
                
                if severity in ("medium", "high") and not existing_alert:
                    # Write to database Alert table
                    alert = models.Alert(
                        user_id=user_id,
                        transaction_id=t.id,
                        alert_type="anomaly",
                        severity=severity,
                        title=f"Unusual transaction at {t.description}",
                        message=explanation or f"₹{abs(t.amount):,.0f} spend flagged as unusual.",
                        is_read=False
                    )
                    db.add(alert)
                    db.commit()
                    db.refresh(alert)
                    
                    anomaly_flags.append({
                        "id": alert.id,
                        "transaction_id": t.id,
                        "description": t.description,
                        "amount": t.amount,
                        "category": t.category,
                        "severity": severity,
                        "anomaly_score": score,
                        "explanation": explanation
                    })
                    
                    if severity == "high":
                        max_severity = "high"
                    elif severity == "medium" and max_severity != "high":
                        max_severity = "medium"
            except Exception as e:
                print(f"[Monitor Node] Scorer failed: {e}")
                
    # 3. Subscription Detection & Creep Monitoring (IsolationForest & Subscription Detection)
    try:
        sub_detector = get_subscription_detector()
        txns_all = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.user_id == user_id,
                models.Transaction.date >= datetime.utcnow() - timedelta(days=180)
            )
            .all()
        )
        if not txns_all:
            txns_all = (
                db.query(models.Transaction)
                .filter(models.Transaction.user_id == user_id)
                .order_by(models.Transaction.date.desc())
                .limit(200)
                .all()
            )
        if txns_all:
            df_sub = pd.DataFrame([{
                "date": t.date,
                "description": t.description,
                "amount": t.amount,
                "category": t.category or "Other"
            } for t in txns_all])
            subs = sub_detector.detect(df_sub)
            user_obj = db.query(models.User).filter(models.User.id == user_id).first()
            income = user_obj.monthly_income if user_obj and user_obj.monthly_income else 50000.0
            creep = sub_detector.subscription_creep_score(subs, income)
            
            # If high-risk subscription creep (>10% income) or high monthly outflow
            if creep.get("risk_level") == "high":
                existing_creep_alert = db.query(models.Alert).filter(
                    models.Alert.user_id == user_id,
                    models.Alert.alert_type == "subscription_creep",
                    models.Alert.is_read == False
                ).first()
                if not existing_creep_alert:
                    alert = models.Alert(
                        user_id=user_id,
                        alert_type="subscription_creep",
                        severity="medium",
                        title="⚠️ Subscription Creep Detected",
                        message=creep.get("insight", "Recurring subscriptions exceed 10% of monthly income."),
                        is_read=False
                    )
                    db.add(alert)
                    db.commit()
                    db.refresh(alert)
                    
                    anomaly_flags.append({
                        "id": alert.id,
                        "transaction_id": None,
                        "description": "Recurring Subscriptions",
                        "amount": creep.get("total_monthly_subscriptions", 0),
                        "category": "Subscriptions",
                        "severity": "medium",
                        "anomaly_score": round(creep.get("income_pct", 10.0) / 100.0, 2),
                        "explanation": creep.get("insight")
                    })
                    if max_severity == "none":
                        max_severity = "medium"
    except Exception as e:
        print(f"[Monitor Node] Subscription check error: {e}")

    return {
        "anomaly_flags": anomaly_flags,
        "severity_reached": max_severity
    }


def explainer_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Explainer Agent (High-Performance Grounded Explanations)
    Generates plain-text explanations for flagged anomalies using:
    - Direct in-memory vector knowledge retrieval (0 LLM overhead)
    - Single consolidated batch prompt (1 fast LLM call instead of multiple sequential calls)
    - Token limits (max_tokens=200, timeout=15s)
    - Instant deterministic ML statistical fallback if LLM times out or is offline
    """
    user_id = state["user_id"]
    flags = state.get("anomaly_flags", [])
    if not flags:
        return {"explanation": "No major anomalies found this period."}
        
    print(f"[Explainer Node] Generating explanations for {len(flags)} alerts...")
    flags_to_explain = flags[:2]  # Focus on top 2 alerts
    items_context = []
    fallback_explanations = []
    
    for f in flags_to_explain:
        amt = abs(f["amount"])
        cat = f.get("category", "General")
        desc = f.get("description", "Unknown Merchant")
        
        # Pull category history (fast DB query)
        history_txns = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.user_id == user_id,
                models.Transaction.category == cat,
                models.Transaction.amount < 0
            )
            .limit(10)
            .all()
        )
        avg_spend = sum(abs(t.amount) for t in history_txns) / len(history_txns) if history_txns else amt
        
        # Direct vector retrieval from Chroma KB (zero LLM calls, <5ms)
        try:
            kb_chunks = retrieve(f"{cat} spending budgeting rules", n_results=1)
            rag_context = kb_chunks[0][0].strip()[:150] if (kb_chunks and kb_chunks[0][2] >= 0.35) else ""
        except Exception:
            rag_context = ""
            
        ml_exp = f.get("explanation") or f"Spend of ₹{amt:,.0f} flagged as unusual."
        
        items_context.append(
            f"- Transaction: {desc}\n"
            f"  Amount: ₹{amt:,.2f}\n"
            f"  Category: {cat} (Historical average: ₹{avg_spend:,.2f})\n"
            f"  ML Signal: {ml_exp}"
            + (f"\n  Guideline Context: {rag_context}" if rag_context else "")
        )
        
        fallback_explanations.append(
            f"**Alert for {desc} (₹{amt:,.0f})**: {ml_exp} "
            f"(Your typical {cat} transaction is ~₹{avg_spend:,.0f}). Please verify if this was intended."
        )

    # Consolidated single batch prompt to LLM (1 call instead of cascading RAG loops)
    prompt = f"""Explain the following flagged transaction(s) to the user in a helpful, calm tone:

{chr(10).join(items_context)}

Instructions:
- Write 1-2 friendly, grounded sentences per alert citing the exact numbers.
- Explain why it was flagged and what to review.
- Format strictly as:
**Alert for [Merchant] (₹[Amount])**: [Explanation]
- Keep the entire output concise (under 150 words total)."""

    try:
        exp_response = _call_llm(
            prompt,
            "You are a friendly, concise financial explainer agent.",
            max_tokens=200,
            timeout_s=15.0
        )
        
        # Verify valid response or use deterministic ML fallback
        if (
            not exp_response
            or exp_response.startswith("[")
            or "Ollama Error" in exp_response
            or "MYFY.AI Autonomous Assistant" in exp_response
        ):
            print("[Explainer Node] LLM unavailable, slow, or errored; returning high-precision ML explanations.")
            return {"explanation": "\n\n".join(fallback_explanations)}
            
        return {"explanation": exp_response.strip()}
    except Exception as e:
        print(f"[Explainer Node] Exception calling LLM: {e}; falling back to ML explanations.")
        return {"explanation": "\n\n".join(fallback_explanations)}


def recommender_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Recommender Agent (Ollama advice generation)
    Examines goals and budget, saves advisory items, returns recommendations.
    """
    user_id = state["user_id"]
    explanation = state.get("explanation", "")
    print(f"[Recommender Node] Analyzing goals for user_id={user_id}")
    
    # 1. Fetch active goals
    goals = db.query(models.Goal).filter(models.Goal.user_id == user_id, models.Goal.is_completed == False).all()
    goals_context = "\n".join([f"- Goal '{g.name}': Target ₹{g.target_amount}, Current ₹{g.current_amount}" for g in goals]) or "No active savings goals."
    
    # 2. Get recent subscription creep analysis
    creep_insight = "No subscription creep detected."
    try:
        user_txns = (
            db.query(models.Transaction)
            .filter(models.Transaction.user_id == user_id)
            .order_by(models.Transaction.date.desc())
            .limit(100)
            .all()
        )
        if user_txns:
            df = pd.DataFrame([
                {
                    "date": t.date,
                    "description": t.description,
                    "amount": t.amount,
                    "category": t.category
                } for t in user_txns
            ])
            sub_detector = get_subscription_detector()
            subs = sub_detector.detect(df)
            user_obj = db.query(models.User).filter(models.User.id == user_id).first()
            income = user_obj.monthly_income if user_obj and user_obj.monthly_income else 50000.0
            creep_data = sub_detector.subscription_creep_score(subs, income)
            creep_insight = creep_data.get("insight", creep_insight)
    except Exception as e:
        print(f"[Recommender Node] Subscription creep analysis error: {e}")
        
    prompt = f"""Based on the user's financial details below, generate 1-2 actionable, advisory savings recommendations:

Goals:
{goals_context}

Subscription Creep Insight:
{creep_insight}

Recent Anomalies/Explanations:
{explanation if explanation else "No anomalies detected."}

Guidelines:
- Provide recommendations as advisory recommendations ONLY.
- Ensure the recommendations directly support the user's active goals.
- Suggest simple steps (e.g. moving a specific amount of ₹ to their Emergency Fund, cutting back on category spending).

Format your output strictly as a JSON list of objects:
[
  {{
    "title": "Short title",
    "message": "Actionable advice message citing specific goals/amounts",
    "priority": "medium"
  }}
]
Do not include any extra text or markdown codeblocks."""

    recs_text = _call_llm(prompt, "You are a financial advisor recommender agent.", max_tokens=250, timeout_s=15.0)
    recommendations = []
    
    try:
        # Strip markdown
        if "```" in recs_text:
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", recs_text)
            if match:
                recs_text = match.group(1).strip()
        
        parsed = json.loads(recs_text)
        for p in parsed:
            # Save to PostgreSQL recommendations table
            rec_db = models.Recommendation(
                user_id=user_id,
                title=p["title"],
                message=p["message"],
                priority=p.get("priority", "medium"),
                is_actioned=False
            )
            db.add(rec_db)
            db.commit()
            db.refresh(rec_db)
            
            recommendations.append({
                "title": rec_db.title,
                "message": rec_db.message,
                "priority": rec_db.priority,
                "is_actioned": False
            })
    except Exception as e:
        db.rollback()  # Protect PostgreSQL session against aborted transaction
        print(f"[Recommender Node] Parsing/DB save failed: {e}. Raw text: {recs_text}")
        try:
            # Add basic fallback recommendation
            rec_db = models.Recommendation(
                user_id=user_id,
                title="Emergency Fund Contribution",
                message="Consider contributing 10% of your discretionary income to your savings goals this week.",
                priority="low",
                is_actioned=False
            )
            db.add(rec_db)
            db.commit()
            recommendations.append({
                "title": rec_db.title,
                "message": rec_db.message,
                "priority": "low",
                "is_actioned": False
            })
        except Exception:
            db.rollback()
        
    return {"recommendations": recommendations}


def synthesizer_node(state: FinAgentState) -> Dict[str, Any]:
    """
    Synthesizer/Orchestrator Node (FastAPI response compilation)
    Generates final response or dispatches proactive webhook to Express gateway.
    """
    trigger = state["trigger"]
    user_message = state["user_message"]
    explanation = state.get("explanation", "")
    recommendations = state.get("recommendations", [])
    history = state.get("history", [])
    user_facts = state.get("user_facts", [])
    
    print(f"[Synthesizer Node] Packaging response for trigger={trigger}")
    
    if trigger == "scheduled_scan":
        # Compile a proactive weekly digest/notification payload
        rec_bullets = "\n".join([f"- **{r['title']}**: {r['message']}" for r in recommendations])
        payload_content = f"### Proactive Financial Review\n\n"
        if explanation:
            payload_content += f"#### ⚠️ Alerts Detected:\n{explanation}\n\n"
        if rec_bullets:
            payload_content += f"#### 💡 Recommendations:\n{rec_bullets}\n"
        else:
            payload_content += "Your budget and goals are on track. Keep it up!\n"
            
        # Deliver to Express gateway
        express_gateway_url = os.getenv("EXPRESS_GATEWAY_URL", "http://localhost:5000")
        try:
            http_requests.post(
                f"{express_gateway_url}/notifications/deliver",
                json={
                    "user_id": state["user_id"],
                    "title": "🎯 MYFY.AI Digest & Alerts",
                    "message": payload_content[:300] + "...",
                    "content": payload_content
                },
                timeout=10
            )
            print("[Synthesizer Node] Notification dispatched to Express gateway successfully.")
        except Exception as e:
            print(f"[Synthesizer Node] Failed to dispatch notification to Express: {e}")
            
        return {"final_response": payload_content}
        
    # User message (interactive chat)
    history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history[-4:]])
    facts_str = "\n".join(user_facts)
    retrieved_context = state.get("retrieved_context", "")
    
    prompt = f"""You are MYFY.AI, an intelligent personal finance assistant for Indian users.
Answer the user's request accurately and directly using their verified financial data.

User Request: "{user_message}"

Verified Financial Data & Context for this Request:
{retrieved_context if retrieved_context else "No specific transaction filter matched. General account active."}

Recent Account Anomalies/Alerts:
{explanation if explanation else "No anomalies detected."}

Savings Recommendations:
{json.dumps(recommendations, indent=2) if recommendations else "None."}

Conversation History:
{history_str}

Instructions:
- Prioritize answering the User Request directly using the Verified Financial Data above.
- If the user asked about subscriptions, list their active subscriptions, monthly totals, and next due dates from the data.
- If the user asked about category spending (e.g., food, shopping), provide the exact amount spent and transaction details from the data.
- If the user asked about recent expenses or an overview, provide the exact numbers from the data.
- Only mention anomalies/alerts if they are relevant to the user's question or if an alert was specifically flagged.
- Use ₹ for currency and keep the response friendly, crisp, and under 250 words."""

    response = _call_llm(prompt, "You are MYFY.AI, a helpful personal finance chatbot.", max_tokens=350, timeout_s=20.0)
    return {"final_response": response}


# ─── LangGraph Orchestrator Class ─────────────────────────────────────────────

class LangGraphPlanner:
    """
    Orchestrator running LangGraph StateGraph inside FastAPI.
    """
    def __init__(self, db: Session, user_id: int, session_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.memory = AgentMemory(db, user_id, self.session_id)
        self.graph = self._compile_graph()
        
    def _compile_graph(self) -> Any:
        # Define the StateGraph workflow
        workflow = StateGraph(FinAgentState)
        
        # Add Nodes (passing DB context to Python node closures)
        workflow.add_node("retriever", lambda state: retriever_node(state, self.db))
        workflow.add_node("monitor", lambda state: monitor_node(state, self.db))
        workflow.add_node("explainer", lambda state: explainer_node(state, self.db))
        workflow.add_node("recommender", lambda state: recommender_node(state, self.db))
        workflow.add_node("synthesizer", synthesizer_node)
        
        # Define routing logic
        def route_after_monitor(state: FinAgentState) -> str:
            severity = state.get("severity_reached", "none")
            if severity in ("medium", "high"):
                return "explainer"
            return "recommender"
            
        # Add edges: retriever -> monitor -> (explainer if high/med) -> recommender -> synthesizer
        workflow.set_entry_point("retriever")
        workflow.add_edge("retriever", "monitor")
        workflow.add_conditional_edges(
            "monitor",
            route_after_monitor,
            {
                "explainer": "explainer",
                "recommender": "recommender"
            }
        )
        workflow.add_edge("explainer", "recommender")
        workflow.add_edge("recommender", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
        
    def respond(self, user_message: str, trigger: str = "user_message") -> Dict[str, Any]:
        """Runs the LangGraph agent for the user request."""
        # 1. Update session memory
        self.memory.add_message("user", user_message)
        
        # 2. Get history and persistent facts
        history = self.memory.get_history()
        facts = self.memory.get_persistent_facts()
        
        # 3. Create initial state
        initial_state: FinAgentState = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_message": user_message,
            "history": history,
            "user_facts": facts,
            "anomaly_flags": [],
            "retrieved_context": "",
            "explanation": None,
            "recommendations": [],
            "final_response": "",
            "trigger": trigger,
            "severity_reached": "none"
        }
        
        # 4. Execute the LangGraph StateGraph
        final_state = self.graph.invoke(initial_state)
        
        # 5. Save assistant response to memory
        self.memory.add_message("assistant", final_state["final_response"])
        
        return {
            "response": final_state["final_response"],
            "sources": [],
            "tool_calls_made": [f"monitor_node({final_state['severity_reached']})"],
            "session_id": self.session_id
        }

    def generate_weekly_digest(self) -> str:
        """Run a proactive scan and return the result."""
        result = self.respond(
            user_message="Provide a weekly financial digest scan.",
            trigger="scheduled_scan"
        )
        return result["response"]
