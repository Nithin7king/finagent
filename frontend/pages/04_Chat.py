"""
FinAgent — AI Chat Page
Full-featured chat interface with the autonomous agent.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import uuid

st.set_page_config(page_title="AI Chat — FinAgent", page_icon="💬", layout="wide")

from frontend.components.api_client import api_chat, api_get_digest

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

# Initialize chat state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())

# ─── Header ──────────────────────────────────────────────────────────────────
col_header, col_actions = st.columns([3, 1])
with col_header:
    st.markdown("# 💬 AI Finance Assistant")
    st.caption("Powered by Gemini AI · RAG-grounded answers · Multi-step autonomous reasoning")

with col_actions:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.chat_session_id = str(uuid.uuid4())
            st.rerun()
    with col_b:
        if st.button("📊 Digest", use_container_width=True):
            with st.spinner("Generating weekly digest..."):
                result = api_get_digest()
            if result:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result.get("digest", "Could not generate digest."),
                    "sources": [],
                    "tools": ["get_transactions", "forecast_spending", "get_anomalies"],
                })
                st.rerun()

st.divider()

# ─── Suggested Questions ──────────────────────────────────────────────────────
if not st.session_state.chat_messages:
    st.markdown("#### 💡 Try asking...")
    suggestions = [
        "What did I spend on food last month?",
        "Am I on track with my savings goals?",
        "Explain my recent anomalous transactions",
        "How much will I spend in the next 30 days?",
        "What are my biggest subscriptions?",
        "How can I save more money?",
        "What is Section 80C and how can I save tax?",
        "Is my savings rate healthy?",
    ]

    cols = st.columns(4)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 4]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_message = suggestion
                st.rerun()

# ─── Chat Messages ────────────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">👤 <b>You</b><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            sources = msg.get("sources", [])
            tools = msg.get("tools", [])

            source_str = ""
            if sources:
                source_str = f'<br><small>📚 Sources: {", ".join(sources)}</small>'
            tool_str = ""
            if tools:
                tool_str = f'<br><small>🔧 Tools used: {", ".join(tools)}</small>'

            st.markdown(
                f'<div class="chat-assistant">🤖 <b>FinAgent</b><br>{msg["content"]}{source_str}{tool_str}</div>',
                unsafe_allow_html=True,
            )

# ─── Input ────────────────────────────────────────────────────────────────────
st.divider()

# Handle pending message from suggestion buttons
pending = st.session_state.pop("pending_message", None)

with st.form("chat_form", clear_on_submit=True):
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "Message",
            value=pending or "",
            placeholder="Ask anything about your finances...",
            label_visibility="collapsed",
        )
    with btn_col:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

if submitted and user_input.strip():
    # Add user message
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input.strip(),
    })

    # Call agent
    with st.spinner("🤔 Agent is reasoning..."):
        response = api_chat(
            message=user_input.strip(),
            session_id=st.session_state.chat_session_id,
        )

    if response:
        # Update session ID (in case backend generated a new one)
        if response.get("session_id"):
            st.session_state.chat_session_id = response["session_id"]

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response.get("response", "I couldn't process your request."),
            "sources": response.get("sources", []),
            "tools": response.get("tool_calls_made", []),
        })
    else:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "Sorry, I encountered an error. Please check that the backend is running.",
            "sources": [],
            "tools": [],
        })

    st.rerun()

# ─── Session Info ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 Agent Info")
    st.caption(f"Session: `{st.session_state.chat_session_id[:8]}...`")
    st.caption(f"Messages: {len(st.session_state.chat_messages)}")
    st.markdown("#### Available Tools")
    tools = [
        "📊 get_transactions",
        "🚨 get_anomalies",
        "🔮 forecast_spending",
        "🎯 check_goal",
        "🔢 calculate",
        "📚 search_knowledge",
    ]
    for t in tools:
        st.caption(t)
