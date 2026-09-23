import pytest
from backend.agent.tools import calculate, TOOL_REGISTRY


def test_calculate_tool_basic():
    """Verify safe calculator handles basic arithmetic and percentages."""
    res = calculate("1000 * 0.15")
    assert "error" not in res
    assert res["result"] == 150.0


def test_calculate_tool_percentage():
    res = calculate("50000 - 20%")
    assert "error" not in res
    assert res["result"] == 40000.0


def test_calculate_tool_security():
    """Verify calculator blocks arbitrary malicious Python builtins."""
    res = calculate("__import__('os').system('dir')")
    assert "error" in res


def test_tool_registry():
    """Verify tool registry contains expected tools."""
    assert "get_transactions" in TOOL_REGISTRY
    assert "get_subscriptions" in TOOL_REGISTRY
    assert "get_anomalies" in TOOL_REGISTRY
    assert "forecast_spending" in TOOL_REGISTRY
