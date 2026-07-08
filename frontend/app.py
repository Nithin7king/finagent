"""
FinAgent — Streamlit Application Entry Point
Manages auth state, navigation, and global CSS theming.
"""
import streamlit as st
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(
    page_title="FinAgent — AI Finance Assistant",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global Dark Theme CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root Variables ── */
:root {
    --bg: #0A0A1A;
    --surface: #12122A;
    --surface-2: #1A1A3A;
    --border: rgba(108, 99, 255, 0.2);
    --primary: #6C63FF;
    --primary-light: #8B85FF;
    --secondary: #FF6584;
    --accent: #43E97B;
    --warning: #FFA500;
    --danger: #FF4B4B;
    --text: #E2E8F0;
    --muted: #64748B;
    --radius: 16px;
    --shadow: 0 8px 32px rgba(0,0,0,0.4);
}

/* ── Base ── */
html, body, .stApp {
    background: linear-gradient(135deg, #0A0A1A 0%, #0D0D25 50%, #0A1628 100%) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ── Sidebar ── */
.st-emotion-cache-1y4p8pa, [data-testid="stSidebar"] {
    background: rgba(18, 18, 42, 0.95) !important;
    border-right: 1px solid var(--border) !important;
    backdrop-filter: blur(20px);
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text) !important;
}

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.1), rgba(255, 101, 132, 0.05)) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    border-color: var(--primary) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(108, 99, 255, 0.2) !important;
}

[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    font-weight: 500 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.3s ease !important;
    font-family: 'Inter', sans-serif !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(108, 99, 255, 0.4) !important;
}

/* ── Inputs ── */
.stTextInput > div > div, .stSelectbox > div > div,
.stNumberInput > div > div, .stTextArea > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}

/* ── DataFrames / Tables ── */
.dataframe, [data-testid="stDataFrame"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}

/* ── Cards ── */
.finagent-card {
    background: linear-gradient(135deg, rgba(26, 26, 58, 0.8), rgba(18, 18, 42, 0.9));
    border: 1px solid rgba(108, 99, 255, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 0.5rem 0;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.finagent-card:hover {
    border-color: rgba(108, 99, 255, 0.5);
    box-shadow: 0 8px 32px rgba(108, 99, 255, 0.15);
}

/* ── Alert Badges ── */
.alert-high { background: rgba(255, 75, 75, 0.15); border-left: 4px solid #FF4B4B; padding: 0.75rem 1rem; border-radius: 0 10px 10px 0; margin: 0.5rem 0; }
.alert-medium { background: rgba(255, 165, 0, 0.15); border-left: 4px solid #FFA500; padding: 0.75rem 1rem; border-radius: 0 10px 10px 0; margin: 0.5rem 0; }
.alert-low { background: rgba(67, 233, 123, 0.15); border-left: 4px solid #43E97B; padding: 0.75rem 1rem; border-radius: 0 10px 10px 0; margin: 0.5rem 0; }

/* ── Chat Bubbles ── */
.chat-user {
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.2), rgba(108, 99, 255, 0.1));
    border: 1px solid rgba(108, 99, 255, 0.3);
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.25rem;
    margin: 0.5rem 0 0.5rem 20%;
    color: #E2E8F0;
}

.chat-assistant {
    background: linear-gradient(135deg, rgba(26, 26, 58, 0.9), rgba(18, 18, 42, 0.8));
    border: 1px solid rgba(67, 233, 123, 0.2);
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.25rem;
    margin: 0.5rem 20% 0.5rem 0;
    color: #E2E8F0;
}

/* ── Progress Bars ── */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
    border-radius: 10px !important;
}

/* ── Headers ── */
h1, h2, h3 { color: var(--text) !important; font-family: 'Inter', sans-serif !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--primary) !important; }

/* ── Plotly Charts ── */
.js-plotly-plot .plotly { border-radius: var(--radius) !important; }

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface-2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 12px !important; padding: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--muted) !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: var(--primary) !important; color: white !important; }

/* ── Logo ── */
.finagent-logo {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF, #43E97B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── KPI Numbers ── */
.kpi-big {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #6C63FF, #43E97B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


# ─── Auth Guard ───────────────────────────────────────────────────────────────
def require_auth():
    """Check if user is authenticated, redirect to login if not."""
    if not st.session_state.get("token"):
        st.warning("⚠️ Please log in to access this page.")
        st.stop()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="finagent-logo">💎 FinAgent</div>', unsafe_allow_html=True)
        st.caption("AI-Powered Finance Assistant")
        st.divider()

        if st.session_state.get("user"):
            user = st.session_state["user"]
            st.markdown(f"👤 **{user.get('name', 'User')}**")
            st.caption(f"📧 {user.get('email', '')}")
            st.caption(f"💰 Income: ₹{user.get('monthly_income', 0):,.0f}/mo")
            st.divider()

            # Unread alerts badge
            try:
                from frontend.components.api_client import api_get_unread_count
                unread = api_get_unread_count()
                if unread > 0:
                    st.markdown(
                        f'<div style="background: rgba(255,75,75,0.15); border: 1px solid rgba(255,75,75,0.4); '
                        f'border-radius: 10px; padding: 0.5rem 1rem; margin-bottom: 0.5rem;">'
                        f'🔔 <b>{unread} unread alert{"s" if unread != 1 else ""}</b></div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                pass

            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.chat_session_id = None
                st.rerun()

        st.divider()
        st.caption("🔒 AES-256 encrypted · JWT secured")
        st.caption("🤖 Powered by Gemini AI + RAG")


render_sidebar()


# ─── Main Content ─────────────────────────────────────────────────────────────
if not st.session_state.get("token"):
    # Login / Register page
    st.markdown("# 💎 FinAgent")
    st.markdown("### AI-Powered Personal Finance Assistant")
    st.markdown(
        "Combining **ML categorization**, **RAG-grounded advice**, and an **autonomous agent** "
        "to give you real-time, proactive financial guidance."
    )
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            st.markdown("#### Welcome back!")
            email = st.text_input("Email", key="login_email", placeholder="demo@finagent.ai")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Demo@123")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Login", use_container_width=True, key="login_btn"):
                    if email and password:
                        from frontend.components.api_client import api_login, api_me
                        result = api_login(email, password)
                        if result:
                            st.session_state.token = result["access_token"]
                            user_data = api_me()
                            st.session_state.user = user_data
                            st.success("✅ Logged in!")
                            st.rerun()
            with col_b:
                if st.button("Try Demo", use_container_width=True, key="demo_btn"):
                    from frontend.components.api_client import api_login, api_me
                    result = api_login("demo@finagent.ai", "Demo@123")
                    if result:
                        st.session_state.token = result["access_token"]
                        user_data = api_me()
                        st.session_state.user = user_data
                        st.success("✅ Logged in as demo user!")
                        st.rerun()

        with tab_register:
            st.markdown("#### Create your account")
            reg_name = st.text_input("Full Name", key="reg_name", placeholder="Arjun Sharma")
            reg_email = st.text_input("Email", key="reg_email", placeholder="your@email.com")
            reg_income = st.number_input("Monthly Income (₹)", key="reg_income", min_value=0, value=50000, step=5000)
            reg_password = st.text_input("Password", type="password", key="reg_pass")

            if st.button("Create Account", use_container_width=True, key="reg_btn"):
                if all([reg_name, reg_email, reg_password]):
                    from frontend.components.api_client import api_register, api_me
                    result = api_register(reg_name, reg_email, reg_password, reg_income)
                    if result:
                        st.session_state.token = result["access_token"]
                        user_data = api_me()
                        st.session_state.user = user_data
                        st.success("✅ Account created! Upload a CSV or use synthetic data.")
                        st.rerun()
                else:
                    st.error("Please fill in all fields.")

    st.divider()
    # Feature highlights
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🤖 **Autonomous Agent**\nMulti-step reasoning with tool calls")
    with col2:
        st.markdown("📊 **ML Insights**\nAuto-categorization & anomaly detection")
    with col3:
        st.markdown("🔍 **RAG Q&A**\nGrounded answers from your transaction data")
    with col4:
        st.markdown("🔒 **Secure**\nAES-256 encrypted, JWT authenticated")

else:
    st.markdown("## 👋 Welcome back!")
    st.markdown("Use the **sidebar** to navigate between pages, or click below:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="finagent-card">📊 <b>Dashboard</b><br>Overview of your finances</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="finagent-card">💬 <b>AI Chat</b><br>Ask anything about your finances</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="finagent-card">🎯 <b>Goals</b><br>Track savings progress</div>', unsafe_allow_html=True)
