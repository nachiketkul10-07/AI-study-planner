"""
ui_helpers.py — All Streamlit rendering functions for AI Study Planner
"""

import streamlit as st
import pandas as pd
from datetime import date
from utils.prompt_builder import MOTIVATIONAL_TIPS, STYLE_PROFILES, compute_summary


# ── Page config & custom CSS ──────────────────────────────────────────────────

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF, #3ECFCF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #888;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #6C63FF;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }

    .day-card {
        background: #1a1a2e;
        border-left: 4px solid #6C63FF;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    .day-card.recovery {
        border-left-color: #3ECFCF;
        background: #0d1f2d;
    }

    .day-card.exam {
        border-left-color: #FF6584;
        background: #2a1a1a;
    }

    .day-card.urgent {
        border-left-color: #FFA500;
    }

    .day-card.critical {
        border-left-color: #FF4500;
    }

    .task-pill {
        display: inline-block;
        background: rgba(108, 99, 255, 0.15);
        color: #a29bfe;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.82rem;
        margin: 2px;
        font-family: 'JetBrains Mono', monospace;
    }

    .summary-metric {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        border: 1px solid rgba(108, 99, 255, 0.3);
    }

    .summary-metric .value {
        font-size: 2rem;
        font-weight: 700;
        color: #6C63FF;
    }

    .summary-metric .label {
        font-size: 0.8rem;
        color: #888;
        margin-top: 4px;
    }

    .tip-box {
        background: rgba(62, 207, 207, 0.08);
        border-left: 3px solid #3ECFCF;
        border-radius: 6px;
        padding: 8px 14px;
        margin: 5px 0;
        font-size: 0.9rem;
        color: #ccc;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6C63FF, #3ECFCF) !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(108, 99, 255, 0.08);
        border-radius: 8px;
        padding: 10px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #3ECFCF);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: opacity 0.2s;
    }

    .stButton > button:hover {
        opacity: 0.88;
        border: none;
        color: white;
    }

    hr {
        border-color: rgba(108, 99, 255, 0.2) !important;
    }

    /* ── Topic input styling ─────────────────────── */
    .topic-hint {
        font-size: 0.78rem;
        color: #666;
        margin-top: -4px;
        margin-bottom: 8px;
    }

    .topic-tag {
        display: inline-block;
        background: rgba(62, 207, 207, 0.12);
        color: #3ECFCF;
        border-radius: 14px;
        padding: 2px 10px;
        font-size: 0.78rem;
        margin: 2px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Feature badge ───────────────────────────── */
    .feature-badges {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }

    .feature-badge {
        display: inline-block;
        background: rgba(108, 99, 255, 0.1);
        border: 1px solid rgba(108, 99, 255, 0.2);
        color: #a29bfe;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.72rem;
        font-weight: 500;
    }

    /* ── Sidebar styling ─────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d1a, #1a1a2e);
    }

    section[data-testid="stSidebar"] .stMarkdown h2 {
        background: linear-gradient(135deg, #6C63FF, #3ECFCF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────

def render_header():
    st.markdown('<div class="main-title">📚 AI Study Planner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Generate a smart, personalised study schedule — no API key needed.</div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <div class="feature-badges">
        <span class="feature-badge">⏱️ Pomodoro Timer</span>
        <span class="feature-badge">📊 Analytics</span>
        <span class="feature-badge">📝 Topics</span>
        <span class="feature-badge">📅 Calendar Export</span>
        <span class="feature-badge">💾 Save & Load</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()


# ── Summary cards ─────────────────────────────────────────────────────────────

def render_summary_cards(schedule: list[dict], daily_hours: float, exam_date: date):
    summary = compute_summary(schedule, daily_hours, exam_date)
    cols = st.columns(4)
    metrics = [
        ("📅 Days Left", summary["total_days"]),
        ("📖 Study Days", summary["study_days"]),
        ("⏱️ Total Hours", f"{summary['total_hours']} h"),
        ("📊 Avg / Day", f"{summary['avg_daily_hours']} h"),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


# ── Bar chart ─────────────────────────────────────────────────────────────────

def render_allocation_chart(subjects: list[str], allocation: dict[str, float]):
    st.markdown("### 📊 Subject Hour Distribution")
    df = pd.DataFrame({
        "Subject": subjects,
        "Allocated Hours": [allocation[s] for s in subjects],
    })
    st.bar_chart(df.set_index("Subject"), color="#6C63FF", use_container_width=True)


# ── Progress tracker ──────────────────────────────────────────────────────────

def render_progress_tracker(schedule: list[dict]):
    st.markdown("### 📈 Progress Tracker")

    study_days = [d for d in schedule if not d.get("is_exam_day")]
    if not study_days:
        st.info("No study days to track yet.")
        return

    total = len(study_days)
    completed_key = "completed_days"

    if completed_key not in st.session_state:
        st.session_state[completed_key] = set()

    completed_count = len(st.session_state[completed_key])
    percent = int((completed_count / total) * 100) if total > 0 else 0

    st.markdown(f"**{completed_count} / {total} days completed — {percent}%**")
    st.progress(percent / 100)

    if percent == 100:
        st.success("🏆 You've completed your entire study plan! Best of luck on exam day!")
    elif percent >= 75:
        st.info("🔥 Almost there — keep the momentum going!")
    elif percent >= 50:
        st.info("💪 Halfway through — great progress!")

    return completed_key


# ── Topic input ───────────────────────────────────────────────────────────────

def render_topic_inputs(subjects: list[str]) -> dict[str, list[str]]:
    """Render topic input fields for each subject. Returns {subject: [topics]}."""
    from utils.validators import parse_topics

    st.markdown('<div class="section-header">📝 Topics / Chapters (Optional)</div>', unsafe_allow_html=True)
    st.caption("Break subjects into topics for more focused scheduling.")

    topics = {}
    for subject in subjects:
        prev_val = st.session_state.get(f"topics_{subject}", "")
        raw = st.text_input(
            label=f"{subject} topics",
            placeholder=f"e.g. Chapter 1, Chapter 2, Chapter 3",
            value=prev_val,
            key=f"topic_input_{subject}",
        )
        parsed = parse_topics(raw)
        if parsed:
            topics[subject] = parsed
            # Show parsed tags
            tags_html = " ".join(f'<span class="topic-tag">{t}</span>' for t in parsed)
            st.markdown(tags_html, unsafe_allow_html=True)
        st.session_state[f"topics_{subject}"] = raw

    return topics


# ── Daily checklist schedule ──────────────────────────────────────────────────

def render_daily_schedule(schedule: list[dict], style: str, include_tips: bool):
    st.markdown("### 🗓️ Daily Study Schedule")

    profile = STYLE_PROFILES[style]
    completed_key = "completed_days"

    if completed_key not in st.session_state:
        st.session_state[completed_key] = set()

    for day in schedule:
        is_exam = day.get("is_exam_day", False)
        is_recovery = day["is_recovery"]
        urgency = day.get("urgency", "relaxed")

        # Choose expander icon
        if is_exam:
            icon = "🎓"
        elif is_recovery:
            icon = "🔄"
        elif urgency == "critical":
            icon = "🔴"
        elif urgency == "urgent":
            icon = "🟠"
        else:
            icon = "📅"

        label = f"{icon} **Day {day['day_number']}** — {day['day_label']}"
        if is_exam:
            label = f"🎓 **EXAM DAY** — {day['day_label']}"

        with st.expander(label, expanded=False):
            if is_recovery:
                st.info("🔄 Recovery Day — light review and rest. You've earned it!")

            # Day completion checkbox (not for exam day)
            if not is_exam:
                day_id = day["day_number"]
                is_done = day_id in st.session_state[completed_key]
                checked = st.checkbox(
                    "✅ Mark this day as complete",
                    value=is_done,
                    key=f"day_complete_{day_id}",
                )
                if checked:
                    st.session_state[completed_key].add(day_id)
                else:
                    st.session_state[completed_key].discard(day_id)

            # Tasks
            if day["tasks"]:
                st.markdown(f"**{profile['session_label']}** — {day['hours']} hrs total")
                st.markdown(f"*{profile['break_note']}*")
                st.markdown("")

                for idx, task in enumerate(day["tasks"]):
                    task_key = f"task_{day['day_number']}_{idx}"
                    topic_str = f" → _{task['topic']}_" if task.get("topic") else ""
                    task_label = f"{task['subject']}{topic_str} — **{task['duration_min']} min**"
                    st.checkbox(task_label, key=task_key)

            else:
                st.write("No tasks scheduled for this day.")

            # Optional motivational tip (one per day, cycling)
            if include_tips and not is_exam:
                tip_idx = (day["day_number"] - 1) % len(MOTIVATIONAL_TIPS)
                tip = MOTIVATIONAL_TIPS[tip_idx]
                st.markdown(f"""
                <div class="tip-box">{tip}</div>
                """, unsafe_allow_html=True)


# ── Download button ───────────────────────────────────────────────────────────

def render_download_button(markdown_content: str, exam_date: date):
    filename = f"study_plan_{exam_date.strftime('%Y%m%d')}.md"
    st.download_button(
        label="💾 Download Study Plan (.md)",
        data=markdown_content.encode("utf-8"),
        file_name=filename,
        mime="text/markdown",
        use_container_width=True,
    )


# ── Error / warning banners ───────────────────────────────────────────────────

def render_error(message: str):
    st.error(message)


def render_warning(message: str):
    st.warning(message)
