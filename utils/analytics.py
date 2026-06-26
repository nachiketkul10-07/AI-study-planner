"""
analytics.py — Analytics Dashboard for AI Study Planner
Uses Plotly for rich, interactive visualisations.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta
import math


# ── Shared theme ──────────────────────────────────────────────────────────────

CHART_COLORS = [
    "#6C63FF", "#3ECFCF", "#FF6584", "#FFA500", "#45B7D1",
    "#96CEB4", "#FFEEAD", "#D4A5FF", "#FF9FF3", "#54A0FF",
    "#5F27CD", "#01A3A4", "#F368E0", "#EE5A24", "#7BED9F",
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, system-ui, sans-serif", color="#ccc"),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(108,99,255,0.2)",
        borderwidth=1,
        font=dict(size=12),
    ),
)


# ── 1. Subject Distribution — Donut Chart ─────────────────────────────────────

def render_subject_distribution(subjects: list[str], allocation: dict[str, float]):
    """Render a donut chart showing subject hour allocation."""
    hours = [allocation[s] for s in subjects]

    fig = go.Figure(data=[go.Pie(
        labels=subjects,
        values=hours,
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(subjects)],
                     line=dict(color="rgba(0,0,0,0.3)", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color="#e0e0e0"),
        hovertemplate="<b>%{label}</b><br>%{value:.1f} hrs (%{percent})<extra></extra>",
    )])

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Subject Distribution", font=dict(size=16, color="#e0e0e0")),
        showlegend=True,
        height=360,
        annotations=[dict(
            text=f"<b>{sum(hours):.0f}</b><br>hrs",
            x=0.5, y=0.5, font_size=18, font_color="#6C63FF",
            showarrow=False,
        )],
    )

    st.plotly_chart(fig, use_container_width=True)


# ── 2. Daily Hours — Area Chart ───────────────────────────────────────────────

def render_daily_hours_chart(schedule: list[dict]):
    """Render an area chart of planned daily study hours."""
    days = [d for d in schedule if not d.get("is_exam_day")]
    if not days:
        st.info("No study days to chart.")
        return

    x_labels = [f"Day {d['day_number']}" for d in days]
    y_hours = [d["hours"] for d in days]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=y_hours,
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.12)",
        line=dict(color="#6C63FF", width=2.5, shape="spline"),
        marker=dict(size=6, color="#6C63FF",
                    line=dict(width=1.5, color="#3ECFCF")),
        hovertemplate="<b>%{x}</b><br>%{y:.1f} hrs<extra></extra>",
    ))

    # Add average line
    avg = sum(y_hours) / len(y_hours) if y_hours else 0
    fig.add_hline(
        y=avg,
        line_dash="dash",
        line_color="rgba(62,207,207,0.5)",
        annotation_text=f"Avg: {avg:.1f}h",
        annotation_font_color="#3ECFCF",
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Daily Study Hours", font=dict(size=16, color="#e0e0e0")),
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="rgba(108,99,255,0.08)",
                   title="Hours", color="#888"),
        height=340,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


# ── 3. Study Intensity Heatmap (GitHub-style) ─────────────────────────────────

def render_study_heatmap(schedule: list[dict]):
    """Render a GitHub-style heatmap calendar of study intensity."""
    days = [d for d in schedule if not d.get("is_exam_day")]
    if not days:
        st.info("No study days to visualise.")
        return

    # Map dates to hours
    date_hours = {}
    for d in days:
        date_hours[d["date"]] = d["hours"]

    # Build week-based grid
    all_dates = sorted(date_hours.keys())
    start = all_dates[0]
    end = all_dates[-1]

    # Pad to full weeks
    start_weekday = start.weekday()  # Mon=0 .. Sun=6
    grid_start = start - timedelta(days=start_weekday)

    total_days_span = (end - grid_start).days + 1
    num_weeks = math.ceil(total_days_span / 7)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    z = []  # 7 rows (days of week) x num_weeks cols
    hover = []
    x_labels = []

    for row in range(7):
        z_row = []
        h_row = []
        for col in range(num_weeks):
            current = grid_start + timedelta(days=col * 7 + row)
            hours = date_hours.get(current, None)
            if hours is not None:
                z_row.append(hours)
                h_row.append(f"{current.strftime('%d %b')}: {hours:.1f}h")
            else:
                z_row.append(None)
                h_row.append("")
        z.append(z_row)
        hover.append(h_row)

    for col in range(num_weeks):
        week_date = grid_start + timedelta(days=col * 7)
        x_labels.append(week_date.strftime("%d %b"))

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x_labels,
        y=day_labels,
        colorscale=[
            [0.0, "rgba(108,99,255,0.06)"],
            [0.25, "rgba(108,99,255,0.2)"],
            [0.5, "rgba(108,99,255,0.4)"],
            [0.75, "rgba(62,207,207,0.6)"],
            [1.0, "#3ECFCF"],
        ],
        hovertext=hover,
        hovertemplate="%{hovertext}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Hours", titlefont=dict(color="#888"),
                       tickfont=dict(color="#888")),
        xgap=3,
        ygap=3,
        connectgaps=False,
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Study Intensity Calendar", font=dict(size=16, color="#e0e0e0")),
        xaxis=dict(side="top", color="#888", showgrid=False),
        yaxis=dict(autorange="reversed", color="#888", showgrid=False),
        height=260,
    )

    st.plotly_chart(fig, use_container_width=True)


# ── 4. Cumulative Progress — Planned vs Completed ────────────────────────────

def render_cumulative_progress(schedule: list[dict], completed_days: set):
    """Render cumulative planned vs completed hours over time."""
    days = [d for d in schedule if not d.get("is_exam_day")]
    if not days:
        st.info("No study days to track.")
        return

    x_labels = []
    planned_cum = []
    completed_cum = []
    p_total = 0
    c_total = 0

    for d in days:
        x_labels.append(f"Day {d['day_number']}")
        p_total += d["hours"]
        planned_cum.append(round(p_total, 1))
        if d["day_number"] in completed_days:
            c_total += d["hours"]
        completed_cum.append(round(c_total, 1))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_labels, y=planned_cum,
        mode="lines",
        name="Planned",
        line=dict(color="#6C63FF", width=2.5, dash="dot"),
        hovertemplate="<b>%{x}</b><br>Planned: %{y:.1f}h<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=x_labels, y=completed_cum,
        mode="lines+markers",
        name="Completed",
        fill="tozeroy",
        fillcolor="rgba(62,207,207,0.08)",
        line=dict(color="#3ECFCF", width=2.5),
        marker=dict(size=5, color="#3ECFCF"),
        hovertemplate="<b>%{x}</b><br>Completed: %{y:.1f}h<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Cumulative Progress", font=dict(size=16, color="#e0e0e0")),
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="rgba(108,99,255,0.08)",
                   title="Cumulative Hours", color="#888"),
        height=360,
    )

    st.plotly_chart(fig, use_container_width=True)


# ── Dashboard wrapper ─────────────────────────────────────────────────────────

def render_analytics_dashboard(
    subjects: list[str],
    allocation: dict[str, float],
    schedule: list[dict],
    completed_days: set,
):
    """Render the complete analytics dashboard in a tabbed layout."""

    st.markdown("## 📊 Analytics Dashboard")

    a1, a2 = st.columns(2)

    with a1:
        render_subject_distribution(subjects, allocation)

    with a2:
        render_daily_hours_chart(schedule)

    render_study_heatmap(schedule)

    render_cumulative_progress(schedule, completed_days)
