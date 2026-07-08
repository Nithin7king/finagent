"""
FinAgent — Transactions Page
Table view, CSV upload, and category correction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Transactions — FinAgent", page_icon="💳", layout="wide")

from frontend.components.api_client import (
    api_get_transactions, api_upload_csv, api_update_transaction, api_train_models
)

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

st.markdown("# 💳 Transactions")
st.caption("View, filter, and manage your transaction history")

# ─── Filters ─────────────────────────────────────────────────────────────────
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    days = st.selectbox("Period", [30, 60, 90, 180, 365], format_func=lambda x: f"Last {x} days")
with filter_col2:
    CATEGORIES = ["All", "Food & Dining", "Transport", "Shopping", "Utilities & Bills",
                  "Healthcare", "Entertainment", "Income", "Investments", "Education", "Travel", "Other"]
    category_filter = st.selectbox("Category", CATEGORIES)
with filter_col3:
    anomaly_only = st.checkbox("Anomalies only 🚨")
with filter_col4:
    per_page = st.selectbox("Per page", [25, 50, 100], index=1)

# ─── Load Transactions ────────────────────────────────────────────────────────
with st.spinner("Loading transactions..."):
    cat = None if category_filter == "All" else category_filter
    data = api_get_transactions(days=days, category=cat, per_page=per_page, anomaly_only=anomaly_only)

if not data:
    st.error("Could not load transactions.")
    st.stop()

txns = data.get("transactions", [])
total = data.get("total", 0)

st.markdown(f"**{total:,} transactions found** (showing {len(txns)})")

# ─── Transaction Table ────────────────────────────────────────────────────────
if txns:
    df = pd.DataFrame(txns)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%b %d, %Y")
    df["amount_fmt"] = df["amount"].apply(lambda x: f"₹{x:,.2f}" if x > 0 else f"-₹{abs(x):,.2f}")
    df["anomaly"] = df["anomaly_label"].apply(lambda x: "🚨" if x else "✅")
    df["confidence"] = df["ml_confidence"].apply(lambda x: f"{x:.0%}" if x else "N/A")

    display_cols = ["date", "description", "amount_fmt", "category", "anomaly", "confidence", "is_subscription"]
    display_df = df[display_cols].rename(columns={
        "date": "Date", "description": "Description", "amount_fmt": "Amount",
        "category": "Category", "anomaly": "Status", "confidence": "ML Conf.",
        "is_subscription": "Subscription",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Subscription": st.column_config.CheckboxColumn("🔄 Sub"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )

    # ─── Export Button ────────────────────────────────────────────────────────
    import requests as _req
    from frontend.components.api_client import API_BASE
    if st.button("⬇️ Export to CSV", use_container_width=False):
        try:
            token = st.session_state.get("token", "")
            r = _req.get(
                f"{API_BASE}/transactions/export",
                headers={"Authorization": f"Bearer {token}"},
                params={"days": days},
                timeout=30,
            )
            if r.ok:
                from datetime import datetime as _dt
                st.download_button(
                    label="📥 Download CSV",
                    data=r.content,
                    file_name=f"transactions_{_dt.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.error("Export failed.")
        except Exception as e:
            st.error(f"Export error: {e}")
else:
    st.info("No transactions found for the selected filters.")

st.divider()

# ─── CSV Upload ───────────────────────────────────────────────────────────────
with st.expander("📂 Upload CSV Statement", expanded=False):
    st.markdown("""
    **Supported formats:** Bank statement exports from HDFC, SBI, ICICI, Axis, etc.
    
    **Required columns:** `date`, `description` (or `narration` / `merchant`), `amount`
    
    **Optional:** `category` — if omitted, ML auto-categorizes
    
    **Amount format:** Positive = credit/income, Negative = debit/expense
    """)

    uploaded = st.file_uploader(
        "Drop your CSV here",
        type=["csv"],
        help="Upload a CSV exported from your bank's net banking portal",
    )

    if uploaded:
        col_preview, col_upload = st.columns([3, 1])
        with col_preview:
            try:
                preview_df = pd.read_csv(uploaded, nrows=5)
                st.markdown("**Preview (first 5 rows):**")
                st.dataframe(preview_df, use_container_width=True)
                uploaded.seek(0)
            except Exception as e:
                st.error(f"Could not preview CSV: {e}")

        with col_upload:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Upload & Categorize", use_container_width=True):
                with st.spinner("Categorizing transactions with ML..."):
                    result = api_upload_csv(uploaded.read(), uploaded.name)
                if result:
                    st.success(f"✅ {result['created']} transactions imported!")
                    if result["errors"]:
                        st.warning(f"⚠️ {result['errors']} rows had errors.")
                    st.rerun()

# ─── Model Training ───────────────────────────────────────────────────────────
with st.expander("🤖 Train ML Models", expanded=False):
    st.markdown("""
    **Personalized anomaly detection:** Train the model on your specific transaction patterns.
    Run this after adding new data for best results.
    """)
    if st.button("🏋️ Train on My Data", use_container_width=False):
        with st.spinner("Training models on your transaction history..."):
            result = api_train_models()
        if result:
            if result.get("trained"):
                st.success(f"✅ {result['message']}")
            else:
                st.warning(result.get("message", "Training failed."))

# ─── Category Correction ─────────────────────────────────────────────────────
with st.expander("✏️ Correct Transaction Category", expanded=False):
    st.markdown("Fix a misclassified transaction to improve future predictions.")
    col1, col2, col3 = st.columns(3)
    with col1:
        txn_id = st.number_input("Transaction ID", min_value=1, step=1)
    with col2:
        new_cat = st.selectbox("New Category", CATEGORIES[1:])  # Exclude "All"
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✔️ Update"):
            result = api_update_transaction(int(txn_id), {"category": new_cat})
            if result:
                st.success(f"✅ Transaction #{txn_id} updated to '{new_cat}'")
                st.rerun()
