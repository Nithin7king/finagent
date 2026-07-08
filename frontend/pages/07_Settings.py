"""
FinAgent — Settings & Profile Page
Update user profile, change password, view account stats, and export data.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import requests

st.set_page_config(page_title="Settings — FinAgent", page_icon="⚙️", layout="wide")

from frontend.components.api_client import (
    api_update_profile, api_change_password, api_get_profile_stats, API_BASE
)

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

user = st.session_state.get("user", {})

st.markdown("# ⚙️ Settings & Profile")
st.caption("Manage your account, preferences, and data")

# ─── Account Stats ────────────────────────────────────────────────────────────
with st.spinner("Loading account stats..."):
    stats = api_get_profile_stats() or {}

s1, s2, s3, s4 = st.columns(4)
s1.metric("📅 Member Since", stats.get("member_since", "N/A"))
s2.metric("💳 Transactions", str(stats.get("transaction_count", 0)))
s3.metric("🎯 Goals", str(stats.get("goal_count", 0)))
s4.metric("🔔 Alerts", str(stats.get("alert_count", 0)))

st.divider()

# ─── Settings Tabs ────────────────────────────────────────────────────────────
tab_profile, tab_password, tab_export, tab_about = st.tabs([
    "👤 Profile", "🔐 Security", "📤 Export Data", "ℹ️ About"
])

# ─── Profile Tab ──────────────────────────────────────────────────────────────
with tab_profile:
    st.markdown("### 👤 Edit Profile")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input(
                "Full Name",
                value=user.get("name", ""),
                placeholder="Your name",
            )
            new_income = st.number_input(
                "Monthly Income (₹)",
                value=float(user.get("monthly_income", 0)),
                min_value=0.0,
                step=5000.0,
                help="Used to calculate your savings rate",
            )
        with col2:
            new_currency = st.selectbox(
                "Currency",
                ["INR", "USD", "EUR", "GBP", "JPY", "AUD"],
                index=["INR", "USD", "EUR", "GBP", "JPY", "AUD"].index(
                    user.get("currency", "INR")
                ) if user.get("currency") in ["INR", "USD", "EUR", "GBP", "JPY", "AUD"] else 0,
            )
            st.markdown("**Email (read-only)**")
            st.code(user.get("email", ""), language=None)

        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        if submitted:
            result = api_update_profile({
                "name": new_name,
                "monthly_income": new_income,
                "currency": new_currency,
            })
            if result:
                # Update session state
                st.session_state["user"] = {**user, **result}
                st.success("✅ Profile updated successfully!")
                st.rerun()

# ─── Password Tab ────────────────────────────────────────────────────────────
with tab_password:
    st.markdown("### 🔐 Change Password")
    st.caption("Uses bcrypt hashing with cost factor 12")

    with st.form("password_form"):
        current_pass = st.text_input("Current Password", type="password", placeholder="Enter current password")
        new_pass = st.text_input("New Password", type="password", placeholder="Minimum 6 characters")
        confirm_pass = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")

        submitted = st.form_submit_button("🔑 Change Password", use_container_width=True, type="primary")
        if submitted:
            if not current_pass or not new_pass:
                st.error("Please fill in all password fields.")
            elif new_pass != confirm_pass:
                st.error("New passwords do not match.")
            elif len(new_pass) < 6:
                st.error("New password must be at least 6 characters.")
            else:
                result = api_change_password(current_pass, new_pass)
                if result and result.get("success"):
                    st.success("✅ Password changed successfully!")
                elif result:
                    st.error(result.get("message", "Password change failed."))

    st.divider()
    st.markdown("### 🛡️ Security Overview")
    security_items = [
        ("✅", "Passwords hashed with bcrypt (cost=12)", "green"),
        ("✅", "JWT tokens expire in 24 hours", "green"),
        ("✅", "Sensitive fields encrypted with AES-256-GCM", "green"),
        ("✅", "All queries filtered by user_id (row-level isolation)", "green"),
        ("✅", "Agent has read-only access (cannot move funds)", "green"),
    ]
    for icon, text, _ in security_items:
        st.markdown(f"**{icon}** {text}")

# ─── Export Tab ──────────────────────────────────────────────────────────────
with tab_export:
    st.markdown("### 📤 Export Your Data")

    col1, col2 = st.columns(2)
    with col1:
        export_days = st.selectbox(
            "Export Period",
            [30, 60, 90, 180, 365],
            format_func=lambda x: f"Last {x} days",
            index=2,
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="finagent-card">
    📄 <b>CSV Export</b> includes:<br>
    • Date, Description, Amount, Category<br>
    • ML-predicted category and confidence<br>
    • Anomaly status and score<br>
    • Subscription detection flag<br>
    • Transaction source (manual / csv / synthetic)
    </div>
    """, unsafe_allow_html=True)

    if st.button("⬇️ Download Transactions CSV", use_container_width=True, type="primary"):
        with st.spinner("Preparing export..."):
            try:
                token = st.session_state.get("token", "")
                r = requests.get(
                    f"{API_BASE}/transactions/export",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"days": export_days},
                    timeout=30,
                )
                if r.ok:
                    from datetime import datetime as _dt
                    fname = f"finagent_{_dt.now().strftime('%Y%m%d')}.csv"
                    st.download_button(
                        label="📥 Click here to save the file",
                        data=r.content,
                        file_name=fname,
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.error("Export failed. Please try again.")
            except Exception as e:
                st.error(f"Export error: {e}")

    st.divider()
    st.markdown("### 🗑️ Data Management")
    st.warning(
        "**Account deletion** is not available in demo mode. "
        "In production, contact support to remove your data."
    )

# ─── About Tab ───────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("### ℹ️ About FinAgent")
    st.markdown("""
    <div class="finagent-card">
    <div class="finagent-logo">💎 FinAgent v1.0</div>
    <p style="margin-top: 0.5rem; color: #94A3B8;">AI-Powered Personal Finance Assistant</p>
    <hr style="border-color: rgba(108,99,255,0.2)">
    <p>Combining <b>ML-based categorization & anomaly detection</b>, <b>RAG-grounded Q&A</b>,
    and an <b>autonomous multi-step agent</b> for proactive, personalized financial guidance.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🛠️ Tech Stack")
    tech = [
        ("🐍 Python 3.10+", "FastAPI · SQLAlchemy · Pydantic · bcrypt"),
        ("🤖 AI/ML", "scikit-learn · sentence-transformers · ChromaDB · Gemini API"),
        ("🎨 Frontend", "Streamlit · Plotly"),
        ("🗄️ Database", "SQLite (AES-256 encrypted fields)"),
        ("⏰ Scheduler", "APScheduler (weekly digest, bill reminders, anomaly scan)"),
    ]
    for name, details in tech:
        col_n, col_d = st.columns([1, 3])
        col_n.markdown(f"**{name}**")
        col_d.markdown(details)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**API Documentation**")
        st.markdown("[FastAPI Docs → http://localhost:8000/docs](http://localhost:8000/docs)")
    with col2:
        st.markdown("**License**")
        st.markdown("MIT — See LICENSE file")
