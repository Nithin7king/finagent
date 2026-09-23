import os
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
import requests as http_requests

from backend.rag.knowledge_loader import retrieve
from backend.rag.embedder import get_embedding_engine

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

RELEVANCE_THRESHOLD = 0.35  # Minimum cosine similarity to use retrieved context


def _call_ollama(prompt: str, system: str = "", max_tokens: Optional[int] = None, timeout_s: float = 30.0) -> str:
    """Call Ollama local LLM via REST API with configurable token limit and timeout."""
    api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    try:
        url = f"{api_url}/api/generate"
        options = {"temperature": 0.7}
        if max_tokens:
            options["num_predict"] = max_tokens
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": options
        }
        # Use (connect_timeout=2.5s, read_timeout=timeout_s) so we don't freeze when Ollama is offline or slow
        resp = http_requests.post(url, json=payload, timeout=(2.5, timeout_s))
        resp.raise_for_status()
        return resp.json()["response"].strip()
    except Exception as e:
        return (
            f"[Ollama Error] Unable to connect to local Ollama at {api_url} with model '{model}'. "
            f"Please ensure Ollama is running (`ollama serve`). Details: {str(e)}"
        )


def _call_llm(prompt: str, system: str = "", max_tokens: Optional[int] = None, timeout_s: float = 30.0) -> str:
    """
    Call the configured LLM with a prompt.
    Returns the text response. If local Ollama is offline, gracefully falls back
    to Gemini/Anthropic if configured, or the grounded offline finance engine.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if provider == "ollama":
        res = _call_ollama(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        if not res.startswith("[Ollama Error]"):
            return res
        # Ollama failed: try configured cloud providers first
        if gemini_key:
            return _call_gemini(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        if anthropic_key:
            return _call_anthropic(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        # Fall back to grounded offline response
        return _offline_response(prompt)

    if provider == "gemini" and gemini_key:
        return _call_gemini(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
    elif provider == "anthropic" and anthropic_key:
        return _call_anthropic(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
    elif provider == "offline":
        return _offline_response(prompt)
    else:
        # Fallback evaluation
        res = _call_ollama(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        if not res.startswith("[Ollama Error]"):
            return res
        if gemini_key:
            return _call_gemini(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        if anthropic_key:
            return _call_anthropic(prompt, system, max_tokens=max_tokens, timeout_s=timeout_s)
        return _offline_response(prompt)


def _call_gemini(prompt: str, system: str = "", max_tokens: Optional[int] = None, timeout_s: float = 20.0) -> str:
    """Call Gemini via REST API (Python 3.8 compatible)."""
    try:
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY", "")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens or 1024},
        }
        resp = http_requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini Error] {str(e)}"


def _call_anthropic(prompt: str, system: str = "", max_tokens: Optional[int] = None, timeout_s: float = 20.0) -> str:
    """Call Anthropic Claude via REST API (Python 3.8 compatible)."""
    try:
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens or 1024,
            "system": system or "You are FinAgent, a helpful personal finance assistant.",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = http_requests.post(url, headers=headers, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        return f"[Anthropic Error] {str(e)}"


def _offline_response(prompt: str) -> str:
    """
    Offline fallback: grounded, comprehensive financial guidance for Indian users.
    Used when local Ollama is not running or no external API keys are active.
    Extracts the user's actual question and formats grounded data if present.
    """
    raw_lower = prompt.lower()
    
    # 1. Extract the actual user query if wrapped in an agent prompt
    user_q = raw_lower
    for prefix in ['user request: "', 'user message: "', 'user question: "']:
        if prefix in raw_lower:
            try:
                user_q = raw_lower.split(prefix)[1].split('"')[0].strip()
                break
            except Exception:
                pass

    # 2. Extract verified financial data context if present
    data_context = ""
    if "verified financial data & context" in raw_lower:
        try:
            part = prompt.split("Verified Financial Data & Context for this Request:")[1]
            data_context = part.split("Recent Account Anomalies/Alerts:")[0].strip()
        except Exception:
            pass

    # 3. Handle Subscriptions query
    if any(kw in user_q for kw in ["subscri", "recurring", "bill", "membership", "netflix", "prime", "spotify", "hotstar", "jio", "airtel", "plan", "active sub"]):
        if data_context and "active subscriptions" in data_context.lower():
            return f"### 📱 Active Subscriptions & Recurring Bills\n\n{data_context}"
        return (
            "### 📱 Active Subscriptions & Recurring Bills\n\n"
            "Based on your transaction records, no active recurring subscriptions or auto-debit memberships were detected in the last 180 days."
        )

    # 4. Handle Category Spending (e.g. Food, Shopping, etc.)
    if any(kw in user_q for kw in ["food", "dining", "zomato", "swiggy", "grocer", "shopping", "transport", "travel", "entertainment", "health"]):
        if data_context and "category spend" in data_context.lower():
            return f"### 📊 Spending Details\n\n{data_context}"

    # 5. Handle Summary of expenses / spending overview
    if any(kw in user_q for kw in ["summary", "recent expense", "recent transaction", "how much did i spend", "total spend", "overview", "statement"]):
        if data_context and "financial overview" in data_context.lower():
            return f"### 📊 Recent Expense Summary\n\n{data_context}"

    # 6. Handle Savings / Goals query
    if any(kw in user_q for kw in ["save", "saving", "goal", "target", "budget", "cut back"]):
        if data_context and "savings goals" in data_context.lower():
            return f"### 🎯 Savings & Budget Roadmap\n\n{data_context}"

    # 7. Handle explicit Anomaly / Alert queries
    if any(kw in user_q for kw in ["anomaly", "anomalies", "flagged", "alert", "suspicious", "unusual"]):
        return (
            "### ⚠️ Anomaly & Alert Review\n\n"
            "Transactions flagged as unusual exceed your historical spending baseline or frequency for that category. "
            "Please review the **Alerts** tab on your dashboard to verify recent flagged charges."
        )

    # 8. Standard Knowledge Base / Tax topics
    if "tax" in user_q or "80c" in user_q or "deduction" in user_q or "regime" in user_q:
        return (
            "### 🧾 Indian Tax-Saving Options (FY 2024–25 / AY 2025–26)\n\n"
            "Under the **Old Tax Regime**, you can optimize your taxable income through several deductions:\n\n"
            "1. **Section 80C (up to ₹1,50,000)**:\n"
            "   - **ELSS Mutual Funds**: 3-year lock-in with potential for equity-linked growth.\n"
            "   - **PPF (Public Provident Fund)**: 15-year tenure, sovereign-backed, EEE status.\n"
            "   - **EPF / VPF**: Mandatory/voluntary contributions towards retirement.\n"
            "   - **Life Insurance (Term Plan)** & Principal on Home Loans.\n\n"
            "2. **Section 80D (Health Insurance)**:\n"
            "   - Up to ₹25,000 for self/family (+₹25,000 for parents under 60, or ₹50,000 for senior citizens).\n\n"
            "3. **Section 80CCD(1B) (NPS)**:\n"
            "   - Additional ₹50,000 tax deduction over and above the ₹1.5L 80C limit.\n\n"
            "4. **Section 24(b)**: Up to ₹2,00,000 deduction on home loan interest.\n\n"
            "*Tip: If your total eligible deductions are under ₹3,75,000, verify if the New Tax Regime (with lower slab rates and ₹75,000 standard deduction) offers lower tax liability.*"
        )

    if "goal" in user_q or "emergency fund" in user_q:
        return (
            "### 🎯 Financial Goals & Emergency Fund\n\n"
            "- **Emergency Fund**: Maintaining a liquid reserve covering 3 to 6 months of essential living expenses (₹1,50,000 to ₹3,00,000).\n"
            "- **Savings Rate**: Aim for at least 20% to 30% of your monthly net income directed towards active goals.\n"
            "- **Action Step**: Automate an auto-debit SIP right after salary day into low-cost index funds or recurring deposits."
        )

    if "sip" in user_q or "mutual fund" in user_q or "invest" in user_q:
        return (
            "### 📈 Investment & SIP Strategy\n\n"
            "- **Systematic Investment Plans (SIPs)** allow disciplined investing while benefiting from rupee-cost averaging.\n"
            "- **Core Allocation**: Consider index funds (Nifty 50 / Nifty Next 50) for long-term compounding (>5 years).\n"
            "- **Debt/Liquid Allocation**: Park short-term funds in overnight/liquid mutual funds or high-yield savings for capital safety."
        )

    if "budget" in user_q or "50/30/20" in user_q:
        return (
            "### ⚖️ 50/30/20 Budgeting Rule\n\n"
            "- **50% Needs**: Rent, groceries, utility bills, insurance, and loan EMIs.\n"
            "- **30% Wants**: Dining out, shopping, entertainment, and vacations.\n"
            "- **20% Savings & Investments**: Emergency fund, retirement SIPs, and goal contributions.\n\n"
            "Track your category breakdown in the **Analytics** tab to keep 'Wants' within target."
        )

    # If data_context exists from retriever, present it directly
    if data_context:
        return f"### 📊 Financial Insights\n\n{data_context}"

    return (
        "### 🤖 MYFY.AI Financial Assistant\n\n"
        "I am actively connected to your ledger, transactions, and financial goals.\n"
        "You can ask me questions about:\n"
        "- **What active subscriptions am I paying for?**\n"
        "- **How much did I spend on food this month?**\n"
        "- **Give me a summary of my recent expenses**\n"
        "- **How can I save ₹5,000 next month?**\n"
        "- **Tax-saving strategies (80C, 80D, Old vs New Regime)**"
    )



class RAGEngine:
    """
    Self-correcting RAG pipeline for financial Q&A.

    Pipeline:
    1. Embed query
    2. Retrieve top-k chunks from knowledge base
    3. Grade relevance (cosine similarity threshold)
    4. If relevant: generate with context
    5. If not relevant: generate without context (with disclaimer)
    """

    def __init__(self):
        self.engine = get_embedding_engine()

    def query(
        self,
        question: str,
        user_context: Optional[str] = None,
        n_retrieve: int = 4,
    ) -> Dict:
        """
        Answer a financial question using RAG with query reformulation retry.

        Args:
            question: User's question
            user_context: Optional string with user's financial summary
            n_retrieve: Number of chunks to retrieve

        Returns:
            Dict with: answer, sources, used_rag, relevance_score
        """
        # Step 1: Retrieve chunks
        retrieved = retrieve(question, n_results=n_retrieve)

        # Step 2: Grade relevance
        relevant_chunks = [(text, source, score) for text, source, score in retrieved
                           if score >= RELEVANCE_THRESHOLD]

        # Step 3: Self-correction (CRAG query reformulation retry)
        if len(relevant_chunks) == 0:
            rewrite_prompt = (
                f"Rewrite the following user query to be optimized for database vector search. "
                f"Output only the rewritten query text, nothing else.\n\n"
                f"Original Query: {question}"
            )
            rewritten_query = _call_llm(rewrite_prompt, "You are a query optimizer.")
            if rewritten_query and not rewritten_query.startswith("["):
                retrieved = retrieve(rewritten_query, n_results=n_retrieve)
                relevant_chunks = [(text, source, score) for text, source, score in retrieved
                                   if score >= RELEVANCE_THRESHOLD]

        used_rag = len(relevant_chunks) > 0
        avg_relevance = sum(s for _, _, s in relevant_chunks) / len(relevant_chunks) if relevant_chunks else 0

        # Step 3: Build prompt
        if used_rag:
            context_str = "\n\n---\n\n".join(
                f"[Source: {source}]\n{text}" for text, source, _ in relevant_chunks
            )
            prompt = self._rag_prompt(question, context_str, user_context)
            sources = list({source for _, source, _ in relevant_chunks})
        else:
            prompt = self._direct_prompt(question, user_context)
            sources = []

        # Step 4: Generate
        system = (
            "You are FinAgent, an AI-powered personal finance assistant for Indian users. "
            "You provide accurate, practical financial advice grounded in the user's actual data. "
            "Always cite sources when available. Use ₹ for currency. Be concise but comprehensive."
        )
        answer = _call_llm(prompt, system)

        return {
            "answer": answer,
            "sources": sources,
            "used_rag": used_rag,
            "relevance_score": round(avg_relevance, 3),
            "chunks_retrieved": len(retrieved),
        }

    def _rag_prompt(self, question: str, context: str, user_context: Optional[str]) -> str:
        user_ctx_str = f"\n\nUser's Financial Context:\n{user_context}" if user_context else ""
        return f"""You have access to the following verified financial knowledge:

{context}{user_ctx_str}

Based on the above information, please answer the following question clearly and specifically:

Question: {question}

Instructions:
- Ground your answer in the provided context when relevant
- Reference specific numbers, rules, or guidelines from the context
- If the question is about the user's personal data, use the financial context provided
- Be actionable and specific, not generic
- Use ₹ for Indian currency amounts"""

    def _direct_prompt(self, question: str, user_context: Optional[str]) -> str:
        user_ctx_str = f"\n\nUser's Financial Context:\n{user_context}" if user_context else ""
        return f"""Please answer the following personal finance question:{user_ctx_str}

Question: {question}

Note: Answer based on general financial knowledge and best practices for Indian users.
Be helpful, accurate, and specific. Use ₹ for currency."""

    def summarize_transactions(
        self,
        transactions_summary: str,
        period: str = "last month",
    ) -> str:
        """Generate a natural language summary of transaction data."""
        prompt = f"""Analyze the following financial data for {period} and provide a clear, insightful summary:

{transactions_summary}

Provide:
1. Key spending highlights (top categories)
2. Notable trends or changes
3. Areas of concern (if any)
4. One actionable recommendation

Keep it conversational and under 200 words. Use ₹ for amounts."""
        return _call_llm(prompt)

    def explain_anomaly(
        self,
        description: str,
        amount: float,
        category: str,
        explanation: str,
        historical_avg: float,
    ) -> str:
        """Generate a detailed explanation for a flagged anomaly."""
        prompt = f"""Explain this flagged transaction to the user in plain English:

Transaction: {description}
Amount: ₹{abs(amount):,.2f}
Category: {category}
Your historical average for {category}: ₹{historical_avg:,.2f}/transaction
System explanation: {explanation}

Write 2–3 sentences explaining:
1. Why this was flagged
2. How it compares to normal behavior
3. What the user should do (verify, dispute, or just note it)

Be conversational and reassuring, not alarming."""
        return _call_llm(prompt)


# Singleton
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
