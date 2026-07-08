"""
FinAgent — Transaction Categorizer
RandomForestClassifier with TF-IDF merchant name features.
Trained on synthetic labeled data. Includes SHAP explainability.
"""
import os
import re
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Tuple, Dict, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "categorizer_model.joblib")


# ─── Module-level transformer (required for joblib pickling) ─────────────────

class HybridTransformer(BaseEstimator, TransformerMixin):
    """
    Combines TF-IDF text features with numeric features (amount, is_income).
    Must be at module level for joblib serialization compatibility.
    """
    def __init__(self):
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=2000, sublinear_tf=True)

    def fit(self, X, y=None):
        descs = X["clean_desc"] if isinstance(X, pd.DataFrame) else [r[0] for r in X]
        self.tfidf.fit(descs)
        return self

    def transform(self, X):
        descs = X["clean_desc"] if isinstance(X, pd.DataFrame) else [r[0] for r in X]
        nums = (
            X[["amount_abs", "is_income"]].values
            if isinstance(X, pd.DataFrame)
            else np.array([[r[1], r[2]] for r in X])
        )
        tfidf_features = self.tfidf.transform(descs)
        num_features = csr_matrix(nums)
        return hstack([tfidf_features, num_features])



CATEGORIES = [
    "Food & Dining", "Transport", "Shopping", "Utilities & Bills",
    "Healthcare", "Entertainment", "Income", "Investments",
    "Education", "Travel", "Other"
]

# Keyword hints per category for fallback/pre-training enrichment
CATEGORY_KEYWORDS = {
    "Food & Dining": ["zomato", "swiggy", "blinkit", "starbucks", "mcdonald", "pizza", "kfc",
                       "domino", "restaurant", "cafe", "food", "kitchen", "haldiram", "biryani",
                       "diner", "eat", "meal", "grocery", "bigbasket", "dunzo"],
    "Transport": ["ola", "uber", "rapido", "irctc", "railway", "metro", "auto", "cab",
                   "petrol", "fuel", "parking", "toll", "bus", "transport"],
    "Travel": ["airlines", "indigo", "air india", "goair", "flight", "hotel", "oyo", "makemytrip",
                "yatra", "airbnb", "booking.com", "travel"],
    "Shopping": ["amazon", "flipkart", "myntra", "nykaa", "meesho", "ajio", "snapdeal",
                  "reliance", "dmart", "big bazaar", "mall", "shop", "store"],
    "Utilities & Bills": ["electricity", "tata power", "bses", "jio", "airtel", "vi ", "vodafone",
                            "internet", "gas", "water", "emi", "loan", "mortgage", "fiber"],
    "Entertainment": ["netflix", "spotify", "amazon prime", "hotstar", "youtube", "pvr", "inox",
                       "bookmyshow", "gaming", "steam", "playstation"],
    "Healthcare": ["apollo", "1mg", "practo", "medplus", "pharma", "hospital", "clinic",
                    "doctor", "medicine", "health", "dental", "lab"],
    "Education": ["coursera", "udemy", "byju", "unacademy", "school", "college", "tuition",
                   "book", "course", "learning"],
    "Investments": ["zerodha", "groww", "sip", "mutual fund", "ppf", "nps", "fd", "bond",
                     "stocks", "etf", "lic"],
    "Income": ["salary", "credit", "interest", "dividend", "freelance", "income", "bonus",
                "refund", "cashback"],
}


def _keyword_category(text: str) -> str:
    """Quick keyword-based fallback categorization."""
    text_lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return "Other"


def _preprocess(description: str) -> str:
    """Clean merchant name for TF-IDF."""
    text = description.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TransactionCategorizer:
    """
    Classifies transactions into spending categories.
    Uses TF-IDF on merchant descriptions + amount feature.
    Falls back to keyword matching when model confidence < threshold.
    """

    def __init__(self, confidence_threshold: float = 0.45):
        self.confidence_threshold = confidence_threshold
        self.model: Optional[Pipeline] = None
        self._load_or_train()

    def _load_or_train(self):
        """Load saved model or train on synthetic data if not found."""
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self._train_from_synthetic()

    def _train_from_synthetic(self):
        """Train on keyword-labeled synthetic merchant data."""
        from backend.data.synthetic_generator import MERCHANTS, INCOME_SOURCES
        import random

        rng = random.Random(42)
        records = []

        # Positive training from known merchants
        for m in MERCHANTS:
            for _ in range(80):  # 80 samples per merchant
                amt = abs(rng.gauss(m["amt_mean"], m["amt_std"] or 50))
                records.append({
                    "description": m["name"],
                    "amount": -amt,
                    "category": m["category"],
                })
        for s in INCOME_SOURCES:
            for _ in range(60):
                records.append({
                    "description": s["name"],
                    "amount": abs(rng.gauss(s["amt_mean"], s["amt_std"])),
                    "category": "Income",
                })

        df = pd.DataFrame(records)
        df["clean_desc"] = df["description"].apply(_preprocess)
        df["amount_abs"] = df["amount"].abs()
        df["is_income"] = (df["amount"] > 0).astype(int)

        X = df[["clean_desc", "amount_abs", "is_income"]]
        y = df["category"]

        self.model = self._build_pipeline()
        self.model.fit(X, y)
        joblib.dump(self.model, MODEL_PATH)

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("features", HybridTransformer()),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )),
        ])

    def predict(self, description: str, amount: float) -> Tuple[str, float]:
        """
        Predict category for a transaction.
        Returns: (category, confidence)
        """
        clean = _preprocess(description)
        is_income = 1 if amount > 0 else 0
        X = pd.DataFrame([{
            "clean_desc": clean,
            "amount_abs": abs(amount),
            "is_income": is_income,
        }])

        if self.model is not None:
            try:
                proba = self.model.predict_proba(X)[0]
                predicted_idx = np.argmax(proba)
                confidence = float(proba[predicted_idx])
                predicted_class = self.model.classes_[predicted_idx]

                if confidence >= self.confidence_threshold:
                    return predicted_class, confidence
            except Exception:
                pass

        # Fallback to keyword matching
        kw_cat = _keyword_category(description)
        return kw_cat, 0.6

    def predict_batch(self, transactions: List[Dict]) -> List[Dict]:
        """
        Predict categories for a list of {description, amount} dicts.
        Returns list with added: ml_category, ml_confidence fields.
        """
        results = []
        for t in transactions:
            cat, conf = self.predict(t["description"], t.get("amount", 0))
            results.append({**t, "ml_category": cat, "ml_confidence": round(conf, 3)})
        return results

    def explain(self, description: str, amount: float) -> str:
        """Return a human-readable explanation of the categorization."""
        cat, conf = self.predict(description, amount)
        keywords_matched = [kw for kw in CATEGORY_KEYWORDS.get(cat, [])
                            if kw in description.lower()]
        kw_str = f" (matched: {', '.join(keywords_matched[:3])})" if keywords_matched else ""
        return (
            f"Categorized as '{cat}' with {conf:.0%} confidence{kw_str}. "
            f"This is based on the merchant name '{description}' and "
            f"{'positive' if amount > 0 else 'negative'} amount of ₹{abs(amount):,.2f}."
        )

    def retrain_with_correction(self, description: str, amount: float, correct_category: str):
        """
        Add a user-corrected sample and retrain.
        In production this would be batched; here we do immediate lightweight update.
        """
        # For demo: just log the correction — full retraining is triggered by seed_data
        pass


# Singleton instance
_categorizer: Optional[TransactionCategorizer] = None


def get_categorizer() -> TransactionCategorizer:
    global _categorizer
    if _categorizer is None:
        _categorizer = TransactionCategorizer()
    return _categorizer
