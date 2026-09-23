import pytest
from backend.agent.planner_langgraph import StateGraph, FinAgentState, retriever_node, monitor_node, synthesizer_node
from backend.rag.engine import _offline_response


def test_offline_response_subscriptions():
    """Verify offline fallback directly addresses subscription queries."""
    resp = _offline_response("What subscriptions am I paying for?")
    assert "subscription" in resp.lower() or "recurring" in resp.lower()


def test_offline_response_food_dining():
    """Verify offline fallback addresses food and dining queries."""
    resp = _offline_response("How much did I spend on food and dining?")
    assert "food" in resp.lower() or "dining" in resp.lower()


def test_graph_state_structure():
    """Verify FinAgentState fields."""
    state = FinAgentState(
        user_id=1,
        session_id="test-session",
        user_message="Hello",
        history=[],
        user_facts=[],
        anomaly_flags=[],
        retrieved_context="",
        explanation=None,
        recommendations=[],
        final_response="",
        trigger="user_message",
        severity_reached="none"
    )
    assert state["user_id"] == 1
    assert state["trigger"] == "user_message"
