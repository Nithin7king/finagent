"""
rag.py
A lightweight, fully-offline RAG implementation using TF-IDF retrieval
(no external embedding API needed - swap in sentence-transformers or
an LLM embedding API for production use).

Retrieves from TWO sources:
  1. The user's own transaction history (dynamic, structured data)
  2. Static financial knowledge documents (tax rules, budgeting frameworks)

Includes a simple "self-check" (Corrective RAG) step: after retrieving,
it scores whether the retrieved context is actually relevant enough to
answer the query before handing it off.
"""

import os
import glob
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")


def _chunk_text(text, chunk_size=350):
    """Naive paragraph-based chunking."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


class KnowledgeRetriever:
    """Retrieves from static financial knowledge docs (tax rules, budgeting guides)."""

    def __init__(self, kb_dir=KB_DIR):
        self.chunks = []
        self.sources = []
        for filepath in glob.glob(os.path.join(kb_dir, "*.txt")):
            with open(filepath, "r") as f:
                text = f.read()
            for chunk in _chunk_text(text):
                self.chunks.append(chunk)
                self.sources.append(os.path.basename(filepath))

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.chunks) if self.chunks else None

    def retrieve(self, query, top_k=2):
        if self.matrix is None:
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        top_idx = np.argsort(sims)[::-1][:top_k]
        results = [
            {"text": self.chunks[i], "source": self.sources[i], "score": float(sims[i])}
            for i in top_idx if sims[i] > 0
        ]
        return results


class TransactionRetriever:
    """Retrieves relevant transactions from the user's own history based on a natural-language query."""

    def __init__(self, df):
        self.df = df.copy()
        # build a searchable text representation of each transaction
        self.df["doc"] = self.df.apply(
            lambda r: f"{r['category']} {r['merchant']} {r['date']} amount {r['amount']} rupees {r['type']}",
            axis=1,
        )
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.df["doc"])

    def retrieve(self, query, top_k=5):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        top_idx = np.argsort(sims)[::-1][:top_k]
        results = self.df.iloc[top_idx].copy()
        results["score"] = sims[top_idx]
        return results[results["score"] > 0]

    def filter_by_category_keyword(self, query):
        """Simple structured fallback: direct category/date filtering, used when semantic search is too weak."""
        query_lower = query.lower()
        matched_categories = [c for c in self.df["category"].unique() if c.lower() in query_lower]
        if matched_categories:
            return self.df[self.df["category"].isin(matched_categories)]
        return pd.DataFrame()


def self_check_relevance(query, retrieved_chunks, min_score=0.05):
    """
    Corrective-RAG style self-check: decides if retrieved context is
    good enough to answer the query, or if the agent should retry /
    fall back to another tool.
    """
    if not retrieved_chunks:
        return False, "No relevant context retrieved."
    best_score = max(c.get("score", 0) for c in retrieved_chunks)
    if best_score < min_score:
        return False, f"Best match score ({best_score:.3f}) below relevance threshold."
    return True, f"Context accepted (best match score {best_score:.3f})."


if __name__ == "__main__":
    from data_gen import generate_transactions

    df = generate_transactions(300, seed=1)

    print("=== Knowledge base retrieval ===")
    kb = KnowledgeRetriever()
    results = kb.retrieve("should I refinance my loan")
    for r in results:
        print(f"[{r['source']}] score={r['score']:.3f}\n{r['text'][:150]}...\n")

    print("=== Transaction retrieval ===")
    tr = TransactionRetriever(df)
    results = tr.retrieve("dining spend")
    print(results[["date", "merchant", "category", "amount", "score"]].head())

    ok, msg = self_check_relevance("refinance my loan", kb.retrieve("refinance loan"))
    print(f"\nSelf-check: {ok} - {msg}")
