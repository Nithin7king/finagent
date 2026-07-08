"""
data_gen.py
Generates realistic synthetic bank transactions to simulate a "live" feed.
No external API/bank access needed - pure Python, fully offline.
"""

import random
import datetime
import pandas as pd

random.seed(42)

CATEGORIES = {
    "Groceries": ["BigBasket", "DMart", "Reliance Fresh", "More Supermarket", "Local Kirana Store"],
    "Dining": ["Zomato", "Swiggy", "Domino's Pizza", "Starbucks", "McDonald's"],
    "Rent": ["Landlord - Monthly Rent"],
    "Utilities": ["BSES Electricity", "Airtel Broadband", "Jio Recharge", "Water Board"],
    "Subscriptions": ["Netflix", "Spotify", "Amazon Prime", "YouTube Premium", "Disney+ Hotstar"],
    "Transport": ["Uber", "Ola Cabs", "Indian Oil Petrol Pump", "Metro Recharge"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "H&M"],
    "Healthcare": ["Apollo Pharmacy", "Practo Consultation", "Local Clinic"],
    "Entertainment": ["PVR Cinemas", "BookMyShow", "INOX"],
    "Loan/EMI": ["HDFC Car Loan EMI", "Personal Loan EMI", "Home Loan EMI"],
    "Investment": ["Zerodha", "Groww SIP", "PPF Deposit"],
    "Income": ["Salary Credit - Employer Pvt Ltd"],
}

# Typical amount ranges per category (min, max) in INR
AMOUNT_RANGES = {
    "Groceries": (300, 3500),
    "Dining": (150, 1500),
    "Rent": (12000, 25000),
    "Utilities": (300, 2500),
    "Subscriptions": (99, 999),
    "Transport": (50, 1200),
    "Shopping": (500, 8000),
    "Healthcare": (200, 5000),
    "Entertainment": (200, 1500),
    "Loan/EMI": (3000, 15000),
    "Investment": (1000, 10000),
    "Income": (45000, 45000),
}


def _random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + datetime.timedelta(days=random_days)


def generate_transactions(n=500, start_date=None, end_date=None, seed=None):
    """Generate n synthetic transactions across categories/dates."""
    if seed is not None:
        random.seed(seed)

    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(days=180)
    if end_date is None:
        end_date = datetime.date.today()

    rows = []
    cats = list(CATEGORIES.keys())
    # weight categories so groceries/dining/subscriptions appear more often than rent/loan
    weights = [12, 14, 3, 6, 10, 10, 10, 5, 6, 3, 4, 3]

    for i in range(n):
        cat = random.choices(cats, weights=weights, k=1)[0]
        merchant = random.choice(CATEGORIES[cat])
        low, high = AMOUNT_RANGES[cat]
        amount = round(random.uniform(low, high), 2) if low != high else float(low)
        date = _random_date(start_date, end_date)
        txn_type = "credit" if cat == "Income" else "debit"
        rows.append({
            "transaction_id": f"TXN{i+1:05d}",
            "date": date.isoformat(),
            "merchant": merchant,
            "category": cat,   # ground-truth label (used to train/evaluate the classifier)
            "amount": amount,
            "type": txn_type,
        })

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def inject_anomalies(df, n_anomalies=8, seed=None):
    """Injects a handful of unusual transactions (fraud/anomaly simulation)."""
    if seed is not None:
        random.seed(seed)
    df = df.copy()
    idxs = random.sample(range(len(df)), min(n_anomalies, len(df)))
    for idx in idxs:
        cat = df.loc[idx, "category"]
        low, high = AMOUNT_RANGES.get(cat, (100, 1000))
        # spike the amount to 5-10x normal range to simulate an anomaly
        df.loc[idx, "amount"] = round(high * random.uniform(5, 10), 2)
    return df


def generate_live_batch(n=5):
    """Simulate a small batch of 'new' transactions arriving right now (for the scheduler demo)."""
    return generate_transactions(n=n, start_date=datetime.date.today(), end_date=datetime.date.today())


if __name__ == "__main__":
    df = generate_transactions(500, seed=42)
    df = inject_anomalies(df, n_anomalies=8, seed=7)
    df.to_csv("/home/claude/finagent/sample_transactions.csv", index=False)
    print(df.head(10))
    print(f"\nGenerated {len(df)} transactions across {df['category'].nunique()} categories.")
