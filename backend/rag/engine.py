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


def _call_ollama(prompt: str, system: str = "") -> str:
    """Call Ollama local LLM via REST API."""
    api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    try:
        url = f"{api_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        resp = http_requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"].strip()
    except Exception as e:
        return (
            f"[Ollama Error] Unable to connect to local Ollama at {api_url} with model '{model}'. "
            f"Please ensure Ollama is running (`ollama serve`) and model is pulled (`ollama pull {model}`). Details: {str(e)}"
        )


def _call_llm(prompt: str, system: str = "") -> str:
    """
    Call the configured LLM with a prompt.
    Returns the text response.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if provider == "ollama":
        res = _call_ollama(prompt, system)
        if res.startswith("[Ollama Error]") and not gemini_key and not anthropic_key:
            return res
        elif not res.startswith("[Ollama Error]"):
            return res

    if provider == "gemini" and gemini_key:
        return _call_gemini(prompt, system)
    elif provider == "anthropic" and anthropic_key:
        return _call_anthropic(prompt, system)
    elif provider == "offline":
        return _offline_response(prompt)
    else:
        # Fallback evaluation
        res = _call_ollama(prompt, system)
        if not res.startswith("[Ollama Error]"):
            return res
        if gemini_key:
            return _call_gemini(prompt, system)
        if anthropic_key:
            return _call_anthropic(prompt, system)
        return _offline_response(prompt)


def _call_gemini(prompt: str, system: str = "") -> str:
    """Call Gemini via REST API (Python 3.8 compatible)."""
    try:
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY", "")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
        resp = http_requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini Error] {str(e)}"


def _call_anthropic(prompt: str, system: str = "") -> str:
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
            "max_tokens": 1024,
            "system": system or "You are FinAgent, a helpful personal finance assistant.",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = http_requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        return f"[Anthropic Error] {str(e)}"


def _offline_response(prompt: str) -> str:
    """
    Offline fallback: rule-based response for common finance queries.
    Used when no LLM API or Ollama model is available.
    """
    prompt_lower = prompt.lower()
    if "emergency fund" in prompt_lower:
        return "An emergency fund should cover 3–6 months of essential expenses, kept in a liquid savings account or liquid mutual fund."
    elif "tax" in prompt_lower and "section 80c" in prompt_lower:
        return "Section 80C allows deductions up to ₹1,50,000 for investments like EPF, PPF, ELSS, NSC, and life insurance premiums."
    elif "sip" in prompt_lower or "mutual fund" in prompt_lower:
        return "SIPs (Systematic Investment Plans) allow you to invest a fixed amount monthly in mutual funds, benefiting from rupee cost averaging."
    elif "budget" in prompt_lower and "50" in prompt_lower:
        return "The 50/30/20 rule: 50% of income for needs, 30% for wants, and 20% for savings and debt repayment."
    else:
        return (
            "I can help you with questions about your spending, savings goals, anomalies, "
            "tax rules, and budgeting strategies. Please start local Ollama ('ollama serve') "
            "or configure an API key in your .env file for full AI-powered responses."
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
