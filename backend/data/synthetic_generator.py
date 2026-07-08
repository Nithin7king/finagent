"""
FinAgent — Synthetic Transaction Generator
Generates 12 months of realistic Indian transaction data.
Includes salary credits, UPI payments, subscriptions, EMIs, and 5% anomalies.
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd


# ─── Indian Merchant / Category Config ───────────────────────────────────────

MERCHANTS: List[Dict] = [
    # Food & Dining
    {"name": "Zomato", "category": "Food & Dining", "amt_mean": 350, "amt_std": 150, "freq_per_month": 8},
    {"name": "Swiggy", "category": "Food & Dining", "amt_mean": 320, "amt_std": 120, "freq_per_month": 6},
    {"name": "Blinkit", "category": "Food & Dining", "amt_mean": 480, "amt_std": 200, "freq_per_month": 5},
    {"name": "Starbucks", "category": "Food & Dining", "amt_mean": 550, "amt_std": 100, "freq_per_month": 3},
    {"name": "McDonald's", "category": "Food & Dining", "amt_mean": 280, "amt_std": 80, "freq_per_month": 4},
    {"name": "Haldiram's", "category": "Food & Dining", "amt_mean": 200, "amt_std": 60, "freq_per_month": 3},
    # Transport
    {"name": "Ola", "category": "Transport", "amt_mean": 180, "amt_std": 80, "freq_per_month": 10},
    {"name": "Uber", "category": "Transport", "amt_mean": 220, "amt_std": 90, "freq_per_month": 8},
    {"name": "Rapido", "category": "Transport", "amt_mean": 80, "amt_std": 30, "freq_per_month": 12},
    {"name": "Indian Railways IRCTC", "category": "Transport", "amt_mean": 850, "amt_std": 400, "freq_per_month": 1},
    {"name": "IndiGo Airlines", "category": "Travel", "amt_mean": 4500, "amt_std": 2000, "freq_per_month": 0.3},
    # Shopping
    {"name": "Amazon", "category": "Shopping", "amt_mean": 1200, "amt_std": 800, "freq_per_month": 5},
    {"name": "Flipkart", "category": "Shopping", "amt_mean": 950, "amt_std": 600, "freq_per_month": 4},
    {"name": "Myntra", "category": "Shopping", "amt_mean": 1400, "amt_std": 700, "freq_per_month": 2},
    {"name": "Nykaa", "category": "Shopping", "amt_mean": 600, "amt_std": 300, "freq_per_month": 1.5},
    {"name": "Meesho", "category": "Shopping", "amt_mean": 450, "amt_std": 200, "freq_per_month": 2},
    # Utilities & Bills
    {"name": "Tata Power Electricity", "category": "Utilities & Bills", "amt_mean": 1800, "amt_std": 400, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "Airtel Mobile", "category": "Utilities & Bills", "amt_mean": 599, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 28},
    {"name": "Jio Fiber", "category": "Utilities & Bills", "amt_mean": 999, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "BSES Rajdhani", "category": "Utilities & Bills", "amt_mean": 1200, "amt_std": 300, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    # Subscriptions (Entertainment)
    {"name": "Netflix", "category": "Entertainment", "amt_mean": 649, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "Spotify", "category": "Entertainment", "amt_mean": 119, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "Amazon Prime", "category": "Entertainment", "amt_mean": 299, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "Hotstar", "category": "Entertainment", "amt_mean": 299, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "YouTube Premium", "category": "Entertainment", "amt_mean": 189, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "PVR Cinemas", "category": "Entertainment", "amt_mean": 600, "amt_std": 200, "freq_per_month": 1.5},
    # Healthcare
    {"name": "Apollo Pharmacy", "category": "Healthcare", "amt_mean": 450, "amt_std": 250, "freq_per_month": 2},
    {"name": "1mg", "category": "Healthcare", "amt_mean": 380, "amt_std": 180, "freq_per_month": 1.5},
    {"name": "Practo Consultation", "category": "Healthcare", "amt_mean": 700, "amt_std": 300, "freq_per_month": 0.5},
    # Education
    {"name": "Coursera", "category": "Education", "amt_mean": 3500, "amt_std": 1000, "freq_per_month": 0.3},
    {"name": "Udemy", "category": "Education", "amt_mean": 499, "amt_std": 200, "freq_per_month": 0.5},
    # Investments
    {"name": "Zerodha SIP", "category": "Investments", "amt_mean": 5000, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "Groww MF", "category": "Investments", "amt_mean": 2000, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    # EMIs
    {"name": "HDFC Home Loan EMI", "category": "Utilities & Bills", "amt_mean": 18000, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
    {"name": "ICICI Car Loan EMI", "category": "Utilities & Bills", "amt_mean": 8500, "amt_std": 0, "freq_per_month": 1, "is_subscription": True, "interval": 30},
]

INCOME_SOURCES = [
    {"name": "Salary Credit - TCS", "amt_mean": 85000, "amt_std": 5000},
    {"name": "Freelance Payment", "amt_mean": 15000, "amt_std": 8000},
    {"name": "Interest Credit SBI", "amt_mean": 1200, "amt_std": 300},
    {"name": "Dividend Credit", "amt_mean": 2500, "amt_std": 1000},
]


def generate_transactions(
    months: int = 12,
    monthly_income: float = 85000.0,
    anomaly_rate: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic transactions for a single user.

    Args:
        months: Number of months of history to generate
        monthly_income: User's approximate monthly income
        anomaly_rate: Fraction of expense transactions to mark as anomalous
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns: date, description, amount, category,
                                 is_subscription, subscription_interval_days, source
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    start_date = datetime.now() - timedelta(days=30 * months)
    transactions = []

    # ── Generate expense transactions ──
    for merchant in MERCHANTS:
        freq = merchant["freq_per_month"]
        is_sub = merchant.get("is_subscription", False)
        interval = merchant.get("interval", 30)

        if is_sub:
            # Subscription: charge on a fixed day each month
            charge_day = rng.randint(1, 28)
            current = start_date.replace(day=min(charge_day, 28))
            while current <= datetime.now():
                jitter_days = rng.randint(-2, 2)
                charge_date = current + timedelta(days=jitter_days)
                if start_date <= charge_date <= datetime.now():
                    amt = abs(rng.gauss(merchant["amt_mean"], merchant["amt_std"] or 0))
                    amt = max(1, round(amt, 2))
                    transactions.append({
                        "date": charge_date,
                        "description": merchant["name"],
                        "amount": -amt,  # expense
                        "category": merchant["category"],
                        "is_subscription": True,
                        "subscription_interval_days": interval,
                        "source": "synthetic",
                        "is_anomaly": False,
                    })
                current += timedelta(days=interval)
        else:
            # Variable frequency: Poisson-distributed
            total_charges = int(freq * months)
            for _ in range(total_charges):
                random_days = rng.randint(0, 30 * months)
                charge_date = start_date + timedelta(days=random_days)
                if charge_date > datetime.now():
                    continue
                amt = abs(rng.gauss(merchant["amt_mean"], merchant["amt_std"] or 50))
                amt = max(1, round(amt, 2))
                transactions.append({
                    "date": charge_date,
                    "description": merchant["name"],
                    "amount": -amt,
                    "category": merchant["category"],
                    "is_subscription": False,
                    "subscription_interval_days": None,
                    "source": "synthetic",
                    "is_anomaly": False,
                })

    # ── Generate income transactions ──
    for month_offset in range(months):
        credit_date = start_date + timedelta(days=30 * month_offset + rng.randint(0, 5))
        if credit_date > datetime.now():
            break
        # Salary (scaled to monthly_income)
        salary_amt = abs(rng.gauss(monthly_income, monthly_income * 0.02))
        transactions.append({
            "date": credit_date,
            "description": INCOME_SOURCES[0]["name"],
            "amount": round(salary_amt, 2),
            "category": "Income",
            "is_subscription": False,
            "subscription_interval_days": None,
            "source": "synthetic",
            "is_anomaly": False,
        })
        # Occasional freelance / interest
        if month_offset % 3 == 0:
            other_income = rng.choice(INCOME_SOURCES[1:])
            amt = abs(rng.gauss(other_income["amt_mean"], other_income["amt_std"]))
            transactions.append({
                "date": credit_date + timedelta(days=rng.randint(5, 15)),
                "description": other_income["name"],
                "amount": round(amt, 2),
                "category": "Income",
                "is_subscription": False,
                "subscription_interval_days": None,
                "source": "synthetic",
                "is_anomaly": False,
            })

    # ── Inject anomalies ──
    expense_indices = [i for i, t in enumerate(transactions) if t["amount"] < 0]
    anomaly_count = int(len(expense_indices) * anomaly_rate)
    anomaly_indices = rng.sample(expense_indices, anomaly_count)

    for idx in anomaly_indices:
        t = transactions[idx]
        # Make amount 3–6× larger than normal
        multiplier = rng.uniform(3, 6)
        transactions[idx]["amount"] = round(t["amount"] * multiplier, 2)
        transactions[idx]["is_anomaly"] = True

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_transactions(months=12)
    print(f"Generated {len(df)} transactions")
    print(f"  Income:   {len(df[df['amount'] > 0])} rows")
    print(f"  Expenses: {len(df[df['amount'] < 0])} rows")
    print(f"  Anomalies: {df['is_anomaly'].sum()} rows")
    print(df.groupby("category")["amount"].sum().sort_values())
