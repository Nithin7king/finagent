"""
FinAgent — Multi-Dataset Training Pipeline
Trains machine learning models across 9 project & Kaggle datasets:
1. Daily Household Transactions (Categorization & Subscriptions)
2. Credit Card Fraud Detection (IsolationForest / RandomForest PCA Fraud Detection)
3. Personal Expense Classification (TF-IDF Merchant Categorizer)
4. Indian Personal Finance & Spending Habits (Time-Series Monthly Spending & Savings Forecaster)
5. Personal Expense Classification Demographics (Budget & Potential Savings Predictor)
6. Synthetic Financial Fraud Dataset (Large-scale Fraud Anomaly Detector)
7. Kaggle: Analyzing Credit Card Spending Habits in India (thedevastator)
8. Kaggle: Income Expenditure Dataset (saurav9786)
9. Kaggle: Monthly Expense Data Statewise (varunraskar)
"""

import os
import sys
import argparse
import joblib
import pandas as pd
import numpy as np
from typing import Optional
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ML_DIR = os.path.join(BASE_DIR, "backend", "ml")

def _resolve_dataset_path(*parts: str) -> str:
    """Resolve dataset path in datasets/ folder or project root."""
    p_nested = os.path.join(BASE_DIR, "datasets", *parts)
    if os.path.exists(p_nested):
        return p_nested
    return os.path.join(BASE_DIR, *parts)

def _find_csv_in_path(path: str) -> Optional[str]:
    """Search for the first .csv file inside a directory."""
    if os.path.isfile(path) and path.endswith(".csv"):
        return path
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".csv"):
                return os.path.join(root, file)
    return None

# ─── Dataset 1: Daily Household Transactions ─────────────────────────────────

def train_daily_household():
    print("\n=======================================================")
    print("1. Training Daily Household Transactions Categorizer...")
    print("=======================================================")
    csv_path = _resolve_dataset_path("Credit Card Transactions Fraud Detection Dataset", "Daily Household Transactions.csv")
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} household records.")

    df = df.dropna(subset=["Category", "Amount"])
    df["clean_text"] = df["Note"].fillna("") + " " + df["Subcategory"].fillna("") + " " + df["Mode"].fillna("")
    df["clean_text"] = df["clean_text"].str.lower().str.strip()

    X = df[["clean_text", "Amount"]]
    y = df["Category"]

    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler

    preprocessor = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(ngram_range=(1, 2), max_features=1500), "clean_text"),
            ("num", StandardScaler(), ["Amount"]),
        ]
    )

    pipeline = Pipeline([
        ("prep", preprocessor),
        ("clf", RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)

    score = pipeline.score(X_test, y_test)
    print(f"Daily Household Categorizer Test Accuracy: {score:.4f}")

    save_path = os.path.join(ML_DIR, "household_categorizer_model.joblib")
    joblib.dump(pipeline, save_path)
    print(f"Model saved to {save_path}")


# ─── Dataset 2: Credit Card Fraud Detection (PCA) ───────────────────────────

def train_creditcard_fraud():
    print("\n=======================================================")
    print("2. Training Credit Card PCA Fraud Detector...")
    print("=======================================================")
    csv_path = _resolve_dataset_path("Credit card Fraud detection", "creditcard.csv")
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} transactions.")

    X = df.drop(columns=["Class"])
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"Credit Card Fraud Model Accuracy: {score:.4f}")

    save_path = os.path.join(ML_DIR, "creditcard_fraud_model.joblib")
    joblib.dump(model, save_path)
    print(f"Model saved to {save_path}")


# ─── Dataset 3: Personal Expense Classification ──────────────────────────────

def train_daily_expense_classifier():
    print("\n=======================================================")
    print("3. Training Personal Expense Classification Model...")
    print("=======================================================")
    csv_path = _resolve_dataset_path("Daily Transactions Dataset", "personal_expense_classification.csv")
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} expense entries.")

    df["text"] = df["merchant"].fillna("") + " " + df["description"].fillna("")
    X = df["text"].str.lower()
    y = df["category"]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", RandomForestClassifier(n_estimators=50, random_state=42))
    ])

    pipeline.fit(X, y)
    print("Personal Expense Classification Model trained successfully.")

    save_path = os.path.join(ML_DIR, "expense_classifier_model.joblib")
    joblib.dump(pipeline, save_path)
    print(f"Model saved to {save_path}")


# ─── Dataset 4: Indian Personal Finance & Spending Habits ───────────────────

def train_indian_spending_forecaster():
    print("\n=======================================================")
    print("4. Training Indian Monthly Spending Forecaster...")
    print("=======================================================")
    csv_path = _resolve_dataset_path("Indian Personal Finance and Spending Habits", "monthly_spending_dataset_2020_2025.csv")
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} monthly observations (2020-2025).")

    df["Month"] = pd.to_datetime(df["Month"])
    df = df.sort_values("Month").reset_index(drop=True)
    df["time_idx"] = np.arange(len(df))

    features = ["time_idx", "Income (₹)"]
    target = "Total Expenditure (₹)"

    X = df[features]
    y = df[target]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    print(f"Spending Forecaster R2 Score: {r2:.4f}")

    save_path = os.path.join(ML_DIR, "indian_monthly_forecaster_model.joblib")
    joblib.dump(model, save_path)
    print(f"Model saved to {save_path}")


# ─── Dataset 5: Demographic Personal Expense Predictor ───────────────────────

def train_demographic_budget_predictor():
    print("\n=======================================================")
    print("5. Training Demographic Budget & Potential Savings Model...")
    print("=======================================================")
    csv_path = _resolve_dataset_path("Personal Expense Classification Dataset", "data.csv")
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} demographic profile records.")

    cat_cols = ["Occupation", "City_Tier"]
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    feature_cols = [c for c in df_encoded.columns if c not in ["Disposable_Income", "Desired_Savings"]]
    X = df_encoded[feature_cols]
    y = df_encoded["Disposable_Income"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=50, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"Demographic Budget Predictor R2 Score: {score:.4f}")

    save_path = os.path.join(ML_DIR, "demographic_budget_model.joblib")
    joblib.dump(model, save_path)
    print(f"Model saved to {save_path}")


# ─── Dataset 6: Synthetic Financial Fraud Dataset ────────────────────────────

def train_synthetic_fraud():
    print("\n=======================================================")
    print("6. Training Synthetic Financial Fraud Detector...")
    print("=======================================================")
    train_csv = _resolve_dataset_path("Synthetic Financial Datasets For Fraud Detection", "fraudTrain.csv")
    if not os.path.exists(train_csv):
        print(f"Error: File not found at {train_csv}")
        return

    print("Loading transaction sample for training...")
    df = pd.read_csv(train_csv, nrows=100000)
    print(f"Loaded {len(df)} training samples.")

    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    df["hour"] = df["trans_date_trans_time"].dt.hour
    df["dayofweek"] = df["trans_date_trans_time"].dt.dayofweek

    features = ["amt", "category", "hour", "dayofweek", "city_pop", "lat", "long", "merch_lat", "merch_long"]
    X = pd.get_dummies(df[features], columns=["category"], drop_first=True)
    y = df["is_fraud"]

    model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X, y)

    score = model.score(X, y)
    print(f"Synthetic Fraud Detection Accuracy: {score:.4f}")

    save_path = os.path.join(ML_DIR, "synthetic_fraud_model.joblib")
    joblib.dump(model, save_path)
    print(f"Model saved to {save_path}")


# ─── Kaggle 1: Indian Credit Card Spending Habits (thedevastator) ─────────────

def train_kaggle_cc_spending_india():
    print("\n=======================================================")
    print("7. Downloading & Training Kaggle: Indian Credit Card Spending Habits...")
    print("=======================================================")
    try:
        import kagglehub
        path = kagglehub.dataset_download("thedevastator/analyzing-credit-card-spending-habits-in-india")
        print("Downloaded dataset path:", path)
        csv_file = _find_csv_in_path(path)
        if not csv_file:
            print("No CSV found in downloaded Kaggle path.")
            return

        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} records from {os.path.basename(csv_file)}.")
        
        # Train categorizer model on City, Card Type, Exp Type, Amount
        target_col = [c for c in df.columns if "Exp" in c or "Category" in c or "Type" in c]
        target = target_col[0] if target_col else df.columns[-1]

        X_cols = [c for c in df.columns if c != target and c not in ["index", "Index"]]
        X = pd.get_dummies(df[X_cols].astype(str), drop_first=True)
        y = df[target].astype(str)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=50, max_depth=12, random_state=42)
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)
        print(f"Kaggle Indian CC Spending Model Accuracy: {score:.4f}")

        save_path = os.path.join(ML_DIR, "kaggle_indian_cc_spending_model.joblib")
        joblib.dump(model, save_path)
        print(f"Model saved to {save_path}")
    except Exception as e:
        print(f"Failed to download/train Kaggle CC spending dataset: {e}")


# ─── Kaggle 2: Income Expenditure Dataset (saurav9786) ───────────────────────

def train_kaggle_income_expenditure():
    print("\n=======================================================")
    print("8. Downloading & Training Kaggle: Income & Expenditure Dataset...")
    print("=======================================================")
    try:
        import kagglehub
        path = kagglehub.dataset_download("saurav9786/incomeexpenditure-dataset")
        print("Downloaded dataset path:", path)
        csv_file = _find_csv_in_path(path)
        if not csv_file:
            print("No CSV found in downloaded Kaggle path.")
            return

        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} records from {os.path.basename(csv_file)}.")

        # Train model to predict Household Expense from Household Income
        target_col = [c for c in df.columns if "Exp" in c or "Expense" in c]
        target = target_col[0] if target_col else df.columns[1]

        X = df.drop(columns=[target]).select_dtypes(include=[np.number])
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)

        r2 = r2_score(y_test, model.predict(X_test))
        print(f"Kaggle Income Expenditure Model R2 Score: {r2:.4f}")

        save_path = os.path.join(ML_DIR, "kaggle_income_expenditure_model.joblib")
        joblib.dump(model, save_path)
        print(f"Model saved to {save_path}")
    except Exception as e:
        print(f"Failed to download/train Kaggle Income Expenditure dataset: {e}")


# ─── Kaggle 3: Monthly Expense Data Statewise (varunraskar) ──────────────────

def train_kaggle_statewise_expense():
    print("\n=======================================================")
    print("9. Downloading & Training Kaggle: Monthly Expense Data Statewise...")
    print("=======================================================")
    try:
        import kagglehub
        path = kagglehub.dataset_download("varunraskar/monthly-expense-data-statewise")
        print("Downloaded dataset path:", path)
        csv_file = _find_csv_in_path(path)
        if not csv_file:
            print("No CSV found in downloaded Kaggle path.")
            return

        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} records from {os.path.basename(csv_file)}.")

        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            target = num_cols[-1]
            df = df.dropna(subset=[target]).fillna(0)
            X = pd.get_dummies(df.drop(columns=[target]), drop_first=True)
            y = df[target]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)

            r2 = r2_score(y_test, model.predict(X_test))
            print(f"Kaggle Statewise Expense Model R2 Score: {r2:.4f}")

            save_path = os.path.join(ML_DIR, "kaggle_statewise_expense_model.joblib")
            joblib.dump(model, save_path)
            print(f"Model saved to {save_path}")
    except Exception as e:
        print(f"Failed to download/train Kaggle statewise expense dataset: {e}")


# ─── CLI Entrypoint ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train ML models on MYFY.AI datasets")
    parser.add_argument(
        "--dataset",
        type=str,
        choices=[
            "household", "cc_fraud", "daily_exp", "indian_finance",
            "personal_expense", "synthetic_fraud", "kaggle_cc_india",
            "kaggle_income_exp", "kaggle_statewise", "all"
        ],
        default="all",
        help="Dataset model to train"
    )

    args = parser.parse_args()

    if args.dataset in ("household", "all"):
        train_daily_household()
    if args.dataset in ("cc_fraud", "all"):
        train_creditcard_fraud()
    if args.dataset in ("daily_exp", "all"):
        train_daily_expense_classifier()
    if args.dataset in ("indian_finance", "all"):
        train_indian_spending_forecaster()
    if args.dataset in ("personal_expense", "all"):
        train_demographic_budget_predictor()
    if args.dataset in ("synthetic_fraud", "all"):
        train_synthetic_fraud()
    if args.dataset in ("kaggle_cc_india", "all"):
        train_kaggle_cc_spending_india()
    if args.dataset in ("kaggle_income_exp", "all"):
        train_kaggle_income_expenditure()
    if args.dataset in ("kaggle_statewise", "all"):
        train_kaggle_statewise_expense()

    print("\n✅ Training complete!")

if __name__ == "__main__":
    main()
