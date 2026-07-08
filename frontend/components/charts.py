"""
FinAgent — Plotly Chart Helpers
Reusable chart components for the Streamlit dashboard.
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import pandas as pd

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#43E97B",
    "warning": "#FFA500",
    "danger": "#FF4B4B",
    "bg": "#0F0F1A",
    "surface": "#1A1A2E",
    "text": "#E2E8F0",
    "muted": "#94A3B8",
    "chart_colors": [
        "#6C63FF", "#FF6584", "#43E97B", "#FFA500", "#00D4FF",
        "#FF61D2", "#FEC89A", "#95E1D3", "#F38181", "#A8E6CF",
        "#FFD93D", "#6BCB77",
    ],
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=COLORS["text"]),
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=True,
)


def spending_donut(by_category: Dict[str, float], title: str = "Spending by Category") -> go.Figure:
    """Donut chart of spending by category."""
    if not by_category:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=COLORS["muted"], size=16))
        fig.update_layout(**LAYOUT_DEFAULTS, title=title)
        return fig

    labels = list(by_category.keys())
    values = list(by_category.values())

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=COLORS["chart_colors"][:len(labels)]),
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))

    total = sum(values)
    fig.add_annotation(
        text=f"₹{total:,.0f}",
        x=0.5, y=0.5,
        font=dict(size=18, color=COLORS["text"], family="Inter"),
        showarrow=False,
    )
    fig.update_layout(**LAYOUT_DEFAULTS, title=title, showlegend=True)
    return fig


def spending_bar(by_category: Dict[str, float], title: str = "Top Spending Categories") -> go.Figure:
    """Horizontal bar chart of spending by category."""
    if not by_category:
        return _empty_chart(title)

    sorted_cats = dict(sorted(by_category.items(), key=lambda x: x[1]))
    labels = list(sorted_cats.keys())
    values = list(sorted_cats.values())

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(
            color=values,
            colorscale=[[0, "#2D2D5A"], [1, COLORS["primary"]]],
            showscale=False,
        ),
        text=[f"₹{v:,.0f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, title=title, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    return fig


def spending_line(monthly_data: List[Dict], title: str = "Monthly Spending Trend") -> go.Figure:
    """Line chart of monthly spending over time."""
    if not monthly_data:
        return _empty_chart(title)

    df = pd.DataFrame(monthly_data)
    fig = go.Figure()

    if "total_expense" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["month"],
            y=df["total_expense"],
            name="Expenses",
            line=dict(color=COLORS["secondary"], width=3),
            fill="tozeroy",
            fillcolor="rgba(255, 101, 132, 0.1)",
            hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        ))

    if "income" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["month"],
            y=df["income"],
            name="Income",
            line=dict(color=COLORS["accent"], width=3),
            hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        ))

    if "savings" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["month"],
            y=df["savings"],
            name="Savings",
            line=dict(color=COLORS["primary"], width=2, dash="dot"),
            hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(**LAYOUT_DEFAULTS, title=title,
                      xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
    return fig


def savings_rate_gauge(savings_rate: float) -> go.Figure:
    """Gauge chart for savings rate."""
    color = COLORS["danger"] if savings_rate < 10 else \
            COLORS["warning"] if savings_rate < 20 else COLORS["accent"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=savings_rate,
        title=dict(text="Savings Rate (%)", font=dict(color=COLORS["text"])),
        delta=dict(reference=20, valueformat=".1f"),
        number=dict(suffix="%", font=dict(color=color)),
        gauge=dict(
            axis=dict(range=[0, 50], tickcolor=COLORS["muted"]),
            bar=dict(color=color),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=COLORS["muted"],
            steps=[
                dict(range=[0, 10], color="rgba(255, 75, 75, 0.15)"),
                dict(range=[10, 20], color="rgba(255, 165, 0, 0.15)"),
                dict(range=[20, 50], color="rgba(67, 233, 123, 0.15)"),
            ],
            threshold=dict(line=dict(color=COLORS["accent"], width=3), value=20),
        ),
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=250, margin=dict(l=30, r=30, t=60, b=20))
    return fig


def forecast_waterfall(forecast_data: Dict, title: str = "30-Day Spending Forecast") -> go.Figure:
    """Waterfall/bar chart for forecast breakdown by category."""
    if not forecast_data or not forecast_data.get("by_category"):
        return _empty_chart(title)

    by_cat = forecast_data["by_category"]
    categories = list(by_cat.keys())
    values = list(by_cat.values())

    if not categories:
        return _empty_chart(title)

    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=COLORS["chart_colors"][:len(categories)],
            line=dict(width=0),
        ),
        text=[f"₹{v:,.0f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Forecast: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS, title=title,
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
    )
    return fig


def anomaly_scatter(transactions_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of transactions with anomalies highlighted."""
    if transactions_df.empty:
        return _empty_chart("Transaction Anomaly Map")

    normal = transactions_df[~transactions_df.get("anomaly_label", pd.Series([False]*len(transactions_df)))]
    anomalies = transactions_df[transactions_df.get("anomaly_label", pd.Series([False]*len(transactions_df)))]

    fig = go.Figure()

    if not normal.empty:
        fig.add_trace(go.Scatter(
            x=normal.get("date", []),
            y=normal.get("amount", []).abs() if hasattr(normal.get("amount", pd.Series()), "abs") else [],
            mode="markers",
            name="Normal",
            marker=dict(color=COLORS["primary"], size=6, opacity=0.6),
            hovertemplate="<b>%{customdata}</b><br>₹%{y:,.0f}<extra></extra>",
            customdata=normal.get("description", []),
        ))

    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies.get("date", []),
            y=anomalies.get("amount", []).abs() if hasattr(anomalies.get("amount", pd.Series()), "abs") else [],
            mode="markers",
            name="Anomaly",
            marker=dict(color=COLORS["danger"], size=10, symbol="x", line=dict(width=2)),
            hovertemplate="<b>%{customdata}</b><br>₹%{y:,.0f}<extra></extra>",
            customdata=anomalies.get("description", []),
        ))

    fig.update_layout(**LAYOUT_DEFAULTS, title="Transaction Anomaly Map",
                      xaxis=dict(showgrid=False),
                      yaxis=dict(title="Amount (₹)", showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
    return fig


def goal_progress_bars(goals: List[Dict]) -> go.Figure:
    """Horizontal progress bars for savings goals."""
    if not goals:
        return _empty_chart("Savings Goals")

    names = [g["name"] for g in goals]
    progress = [min(g.get("progress_pct", 0), 100) for g in goals]
    remaining = [max(100 - p, 0) for p in progress]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=progress,
        y=names,
        orientation="h",
        name="Saved",
        marker=dict(color=COLORS["primary"]),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% complete<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=remaining,
        y=names,
        orientation="h",
        name="Remaining",
        marker=dict(color="rgba(255,255,255,0.1)"),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% remaining<extra></extra>",
    ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="Savings Goal Progress",
        barmode="stack",
        xaxis=dict(range=[0, 100], showgrid=False, ticksuffix="%"),
        yaxis=dict(showgrid=False),
    )
    return fig


def _empty_chart(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="No data available",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=COLORS["muted"], size=16),
    )
    fig.update_layout(**LAYOUT_DEFAULTS, title=title)
    return fig
