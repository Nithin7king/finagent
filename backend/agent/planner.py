"""
FinAgent — Autonomous Agent Planner
Custom plan→act→observe→respond loop with multi-step reasoning.
Orchestrates tools, memory, and RAG to answer user queries.
"""
import json
import re
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.agent.tools import TOOL_REGISTRY, get_transactions, get_anomalies
from backend.agent.tools import forecast_spending, check_goal, calculate, search_knowledge
from backend.agent.memory import AgentMemory
from backend.rag.engine import get_rag_engine, _call_llm

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are FinAgent, an autonomous AI personal finance assistant for Indian users.
You have access to the user's actual financial data and a knowledge base of tax rules, budgeting strategies, and investing guidelines.

Your capabilities:
- Analyze spending patterns, income, and savings from real transaction data
- Detect and explain anomalous transactions
- Forecast future spending based on historical trends
- Track progress toward savings goals
- Provide grounded advice based on verified financial knowledge
- Perform calculations

You MUST:
- Always respond in clear, concise Indian English
- Use ₹ for all currency amounts
- Be proactive — if you notice concerning patterns, mention them
- Ground advice in the user's actual data, not generic statements
- Always be helpful and reassuring, not alarming

You can call tools to get data. When you have enough information, provide a final response."""

PLANNING_PROMPT_TEMPLATE = """
You are analyzing a user's finance question to decide what tools to call.

User question: "{question}"

Conversation history:
{history}

Persistent facts about this user:
{facts}

Available tools:
{tool_list}

Think step by step:
1. What does the user want to know?
2. Which tool(s) should I call first?
3. What parameters should I use?

Respond with a JSON object like this:
{{
  "reasoning": "brief explanation of your plan",
  "tool_calls": [
    {{"tool": "tool_name", "params": {{"param1": value1}}}},
    ...
  ]
}}

If no tools are needed (e.g., simple greeting or knowledge question), respond with:
{{
  "reasoning": "no tools needed",
  "tool_calls": []
}}

Return ONLY valid JSON, no markdown.
"""

RESPONSE_PROMPT_TEMPLATE = """
You are FinAgent, a personal finance assistant. Synthesize the tool results below into a helpful response.

User question: "{question}"

Tool results:
{tool_results}

RAG context (if relevant):
{rag_context}

Conversation history:
{history}

Persistent user facts:
{facts}

Instructions:
- Give a direct, helpful answer to the user's question
- Use specific numbers from the tool results
- Be conversational and actionable
- Use ₹ for currency
- Add relevant financial tips if appropriate
- Keep response under 300 words unless detail is needed
"""


class AgentPlanner:
    """
    Autonomous agent using plan→act→observe→respond loop.
    Coordinates tool calls, memory, and RAG to answer queries.
    """

    def __init__(self, db: Session, user_id: int, session_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.memory = AgentMemory(db, user_id, self.session_id)
        self.rag = get_rag_engine()

    def _format_tools(self) -> str:
        lines = []
        for name, info in TOOL_REGISTRY.items():
            lines.append(f"- {name}: {info['description']} (params: {', '.join(info['params'])})")
        return "\n".join(lines)

    def _parse_tool_calls(self, response_text: str) -> List[Dict]:
        """Extract tool calls from LLM JSON response."""
        try:
            # Handle markdown code blocks
            text = response_text.strip()
            if "```" in text:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if match:
                    text = match.group(1).strip()

            data = json.loads(text)
            return data.get("tool_calls", [])
        except (json.JSONDecodeError, KeyError):
            return []

    def _execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute a named tool with given parameters."""
        if tool_name not in TOOL_REGISTRY:
            return {"error": f"Unknown tool: {tool_name}"}

        tool_info = TOOL_REGISTRY[tool_name]
        fn = tool_info["fn"]

        try:
            if tool_info["requires_db"]:
                return fn(db=self.db, user_id=self.user_id, **params)
            else:
                return fn(**params)
        except Exception as e:
            return {"error": f"Tool '{tool_name}' failed: {str(e)}"}

    def respond(self, user_message: str) -> Dict[str, Any]:
        """
        Main entry point. Process user message through plan→act→observe→respond loop.

        Returns:
            Dict with: response, sources, tool_calls_made, session_id
        """
        # Store user message in memory
        self.memory.add_message("user", user_message)

        history = self.memory.format_history_for_prompt()
        facts = "\n".join(self.memory.get_persistent_facts()) or "No stored facts yet."

        tool_results = {}
        tools_used = []
        iteration = 0

        # ── Phase 1: Planning ──
        planning_prompt = PLANNING_PROMPT_TEMPLATE.format(
            question=user_message,
            history=history,
            facts=facts,
            tool_list=self._format_tools(),
        )
        plan_response = _call_llm(planning_prompt, SYSTEM_PROMPT)
        planned_calls = self._parse_tool_calls(plan_response)

        # ── Phase 2: Act (execute tools) ──
        while iteration < MAX_ITERATIONS and planned_calls:
            for call in planned_calls:
                tool_name = call.get("tool")
                params = call.get("params", {})
                if not tool_name:
                    continue

                result = self._execute_tool(tool_name, params)
                tool_results[tool_name] = result
                tools_used.append(tool_name)

            # After first round of tools, check if more calls are needed
            # For simplicity, we run one round of planned calls
            break

        # ── Phase 3: RAG retrieval ──
        rag_result = self.rag.query(
            question=user_message,
            user_context=self._build_user_context(tool_results),
        )
        rag_context = rag_result.get("answer", "") if rag_result.get("used_rag") else ""
        sources = rag_result.get("sources", [])

        # ── Phase 4: Respond ──
        tool_results_str = json.dumps(tool_results, indent=2, default=str) if tool_results else "No tools called."

        response_prompt = RESPONSE_PROMPT_TEMPLATE.format(
            question=user_message,
            tool_results=tool_results_str[:3000],  # Truncate to avoid token limits
            rag_context=rag_context[:1500] if rag_context else "No relevant knowledge base context.",
            history=history,
            facts=facts,
        )

        if tool_results or rag_context:
            final_response = _call_llm(response_prompt, SYSTEM_PROMPT)
        else:
            # Direct RAG-only answer
            final_response = rag_result.get("answer", "I couldn't find relevant information. Please try rephrasing your question.")

        # Store assistant response
        self.memory.add_message("assistant", final_response)

        # Update persistent facts if we learned something
        if tool_results.get("get_transactions"):
            txn_data = tool_results["get_transactions"]
            if isinstance(txn_data, dict) and "total_income" in txn_data:
                if txn_data["total_income"] > 0:
                    fact = f"User's monthly income is approximately ₹{txn_data['total_income']/3:,.0f} (based on 90-day data)"
                    self.memory.save_persistent_fact(fact)

        return {
            "response": final_response,
            "sources": sources,
            "tool_calls_made": tools_used,
            "session_id": self.session_id,
        }

    def _build_user_context(self, tool_results: Dict) -> str:
        """Build a concise user context string from tool results for RAG."""
        if not tool_results:
            return ""
        lines = []
        if "get_transactions" in tool_results:
            td = tool_results["get_transactions"]
            if isinstance(td, dict) and "total_expenses" in td:
                lines.append(f"- Recent expenses: ₹{td.get('total_expenses', 0):,.0f}")
                lines.append(f"- Recent income: ₹{td.get('total_income', 0):,.0f}")
                lines.append(f"- Savings rate: {td.get('savings_rate', 0)}%")
        if "get_anomalies" in tool_results:
            ad = tool_results["get_anomalies"]
            if isinstance(ad, dict):
                lines.append(f"- Anomalies detected: {ad.get('count', 0)}")
        if "forecast_spending" in tool_results:
            fd = tool_results["forecast_spending"]
            if isinstance(fd, dict):
                lines.append(f"- 30-day forecast: ₹{fd.get('predicted_total_expense', 0):,.0f}")
        return "\n".join(lines) if lines else ""

    def generate_weekly_digest(self) -> str:
        """Generate a proactive weekly spending digest."""
        txn_data = get_transactions(self.db, self.user_id, days=7)
        forecast_data = forecast_spending(self.db, self.user_id, horizon_days=30)
        anomaly_data = get_anomalies(self.db, self.user_id, days=7)

        prompt = f"""Generate a concise weekly financial digest for the user:

Last 7 days:
{json.dumps(txn_data, indent=2, default=str)[:1500]}

30-day forecast:
{json.dumps(forecast_data, indent=2, default=str)[:800]}

Anomalies this week:
{json.dumps(anomaly_data, indent=2, default=str)[:800]}

Format as:
📊 **Weekly Financial Digest**
- This week's spending: ...
- Top categories: ...
- Savings this week: ...
- 🔮 Next 30 days forecast: ...
- ⚠️ Alerts (if any): ...
- 💡 Tip: ...

Be specific with ₹ amounts. Keep it under 200 words."""

        return _call_llm(prompt, SYSTEM_PROMPT)
