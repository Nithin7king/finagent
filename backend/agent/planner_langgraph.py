"""
FinAgent — Multi-Agent Orchestrator via LangGraph
Defines StateGraph, nodes, conditional edges, and execution triggers.
"""
import os
import json
import uuid
import requests as http_requests
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Optional, Any, Literal
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from backend import models
from backend.agent.memory import AgentMemory
from backend.agent.tools import get_transactions, get_anomalies, forecast_spending
from backend.rag.engine import get_rag_engine, _call_llm
from backend.ml.anomaly_detector import get_detector
from backend.ml.subscription_detector import get_subscription_detector

# ─── State Definition ─────────────────────────────────────────────────────────

class Message(TypedDict):
    role: str
    content: str


class AnomalyFlag(TypedDict):
    id: Optional[int]
    transaction_id: int
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

def monitor_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Monitor Agent (Deterministic ML scorer + subscription check)
    Runs without LLM call. Generates alerts.
    """
    user_id = state["user_id"]
    print(f"[Monitor Node] Running continuous checks for user_id={user_id}")
    
    # 1. Fetch transactions from the last 7 days
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.date >= datetime.utcnow() - timedelta(days=7)
        )
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
                
    return {
        "anomaly_flags": anomaly_flags,
        "severity_reached": max_severity
    }


def explainer_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Explainer Agent (RAG + Ollama)
    Generates plain-text explanations for flagged anomalies.
    """
    user_id = state["user_id"]
    flags = state["anomaly_flags"]
    if not flags:
        return {"explanation": "No major anomalies found this period."}
        
    print(f"[Explainer Node] Generating explanations for {len(flags)} alerts...")
    rag = get_rag_engine()
    explanations = []
    
    for f in flags:
        # Query context
        q = f"explain anomaly for {f['description']} in {f['category']} amount {abs(f['amount'])}"
        rag_res = rag.query(q, user_context=f"Transaction category: {f['category']}, amount: {f['amount']}")
        rag_context = rag_res.get("answer", "")
        
        # Pull category history
        history_txns = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.user_id == user_id,
                models.Transaction.category == f["category"],
                models.Transaction.amount < 0
            )
            .limit(10)
            .all()
        )
        avg_spend = sum(abs(t.amount) for t in history_txns) / len(history_txns) if history_txns else abs(f["amount"])
        
        # Ollama generation prompt
        prompt = f"""Explain this flagged transaction to the user:
Merchant: {f['description']}
Amount: ₹{abs(f['amount']):,.2f}
Category: {f['category']}
Your historical average for {f['category']}: ₹{avg_spend:,.2f}/transaction
ML Explanation: {f['explanation']}
RAG Reference rules: {rag_context}

Write a 2-3 sentence grounded explanation citing the exact numbers. Explain why it was flagged and what they should check. Keep the tone helpful, not alarming."""
        
        exp = _call_llm(prompt, "You are a friendly financial explainer agent.")
        explanations.append(f"**Alert for {f['description']} (₹{abs(f['amount']):,.0f})**: {exp}")
        
    return {
        "explanation": "\n\n".join(explanations)
    }


def recommender_node(state: FinAgentState, db: Session) -> Dict[str, Any]:
    """
    Recommender Agent (Ollama advice generation)
    Examines goals and budget, saves advisory items, returns recommendations.
    """
    user_id = state["user_id"]
    explanation = state.get("explanation", "")
    print(f"[Recommender Node] Analyzing goals for user_id={user_id}")
    
    # 1. Fetch active goals
    goals = db.query(models.Goal).filter(models.User.id == user_id, models.Goal.is_completed == False).all()
    goals_context = "\n".join([f"- Goal '{g.name}': Target ₹{g.target_amount}, Current ₹{g.current_amount}" for g in goals]) or "No active savings goals."
    
    # 2. Get recent subscription creep analysis
    creep_score = "0"
    try:
        df = pd.DataFrame() # subscription detector uses historical dataframe
        # Fallback to local warning representation
    except Exception:
        pass
        
    prompt = f"""Based on the user's financial details below, generate 1-2 actionable, advisory savings recommendations:

Goals:
{goals_context}

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

    recs_text = _call_llm(prompt, "You are a financial advisor recommender agent.")
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
        print(f"[Recommender Node] Parsing/DB save failed: {e}. Raw text: {recs_text}")
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
    
    prompt = f"""You are MYFY.AI, a personal finance assistant. Synthesize the findings into a direct chat response.

User message: "{user_message}"

Conversation History:
{history_str}

User Persistent Profile:
{facts_str}

Anomalies/Alerts this period:
{explanation if explanation else "No anomalies detected."}

Recommendations:
{json.dumps(recommendations, indent=2)}

Instructions:
- Provide a friendly, conversational, and direct response to the user.
- If they asked a direct question, answer it using the data.
- If recommendations or explanations exist, weave them in naturally.
- Keep the response short (under 250 words) and use ₹."""

    response = _call_llm(prompt, "You are MYFY.AI, a helpful personal finance chatbot.")
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
            
        # Add edges
        workflow.set_entry_point("monitor")
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
