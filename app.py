"""
app.py — AI Study Planner — Main Streamlit Application
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date, timedelta

from utils.validators import (
    parse_subjects,
    validate_subjects,
    validate_exam_date,
    validate_study_hours,
    validate_topics,
    days_remaining,
    get_urgency_level,
)
from utils.prompt_builder import (
    allocate_hours,
    build_daily_schedule,
    build_markdown_export,
    STYLE_PROFILES,
)
from utils.ui_helpers import (
    apply_custom_css,
    render_header,
    render_summary_cards,
    render_allocation_chart,
    render_progress_tracker,
    render_daily_schedule,
    render_download_button,
    render_topic_inputs,
    render_error,
    render_warning,
)
from utils.pomodoro import render_pomodoro_timer
from utils.analytics import render_analytics_dashboard
from utils.calendar_export import render_calendar_download
from utils.storage import render_save_load_sidebar, auto_save_progress

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_custom_css()

# ── Session state initialisation ──────────────────────────────────────────────

def init_session_state():
    defaults = {
        "schedule_generated": False,
        "schedule": [],
        "subjects": [],
        "difficulties": {},
        "exam_date": None,
        "daily_hours": 3.0,
        "style": "Balanced",
        "include_recovery": True,
        "include_tips": True,
        "allocation": {},
        "markdown_export": "",
        "completed_days": set(),
        "topics": {},
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# ── Sidebar — Save & Load ────────────────────────────────────────────────────

render_save_load_sidebar()

# ── Header ────────────────────────────────────────────────────────────────────

render_header()

# ── Two-column layout ─────────────────────────────────────────────────────────

left_col, right_col = st.columns([1, 2], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
#  LEFT COLUMN — Inputs
# ══════════════════════════════════════════════════════════════════════════════

with left_col:
    st.markdown("## ✏️ Plan Settings")

    # ── Subjects input ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📖 Subjects</div>', unsafe_allow_html=True)
    raw_subjects = st.text_input(
        label="Enter subjects (comma-separated)",
        placeholder="e.g. Mathematics, Physics, History",
        help="Separate each subject with a comma.",
    )

    subjects = parse_subjects(raw_subjects)

    # ── Difficulty sliders (dynamic) ───────────────────────────────────────────
    difficulties = {}
    if subjects:
        st.markdown('<div class="section-header">🎯 Difficulty Levels</div>', unsafe_allow_html=True)
        st.caption("Rate how difficult each subject is for you (1 = easy, 5 = very hard)")
        for subject in subjects:
            prev_val = st.session_state["difficulties"].get(subject, 3)
            difficulties[subject] = st.slider(
                label=subject,
                min_value=1,
                max_value=5,
                value=prev_val,
                key=f"diff_{subject}",
            )
        st.session_state["difficulties"] = difficulties
    else:
        st.caption("👆 Enter subjects above to set difficulty levels.")

    # ── Topic breakdown (NEW) ──────────────────────────────────────────────────
    topics = {}
    if subjects:
        st.divider()
        topics = render_topic_inputs(subjects)

    st.divider()

    # ── Exam date ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📅 Exam / Deadline Date</div>', unsafe_allow_html=True)
    min_date = date.today() + timedelta(days=1)
    default_date = date.today() + timedelta(days=14)

    exam_date = st.date_input(
        label="Select your exam date",
        value=default_date,
        min_value=min_date,
        help="Must be at least 1 day in the future.",
    )

    # ── Daily study hours ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⏱️ Daily Study Hours</div>', unsafe_allow_html=True)
    daily_hours = st.slider(
        label="Hours per day",
        min_value=0.5,
        max_value=12.0,
        value=st.session_state["daily_hours"],
        step=0.5,
        format="%.1f hrs",
    )

    # ── Study style ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🎨 Study Style</div>', unsafe_allow_html=True)
    style = st.selectbox(
        label="Choose your study style",
        options=list(STYLE_PROFILES.keys()),
        index=list(STYLE_PROFILES.keys()).index(st.session_state["style"]),
        help="Each style distributes your hours differently across the days.",
    )
    st.caption(f"*{STYLE_PROFILES[style]['description']}*")

    st.divider()

    # ── Toggles ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚙️ Options</div>', unsafe_allow_html=True)

    include_recovery = st.toggle(
        label="🔄 Include Recovery / Buffer Days",
        value=st.session_state["include_recovery"],
        help="Adds a light review day every 6 study days.",
    )

    include_tips = st.toggle(
        label="💡 Include Motivational Tips",
        value=st.session_state["include_tips"],
        help="Shows a motivational tip for each day of your schedule.",
    )

    st.divider()

    # ── Generate button ────────────────────────────────────────────────────────
    generate_clicked = st.button("🚀 Generate My Study Plan", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  GENERATE LOGIC
# ══════════════════════════════════════════════════════════════════════════════

if generate_clicked:
    # Reset completed days on new generation
    st.session_state["completed_days"] = set()

    # Validate all inputs
    valid_subjects, err_subjects = validate_subjects(subjects)
    valid_date, err_date = validate_exam_date(exam_date)
    valid_hours, err_hours = validate_study_hours(daily_hours)
    valid_topics, err_topics = validate_topics(topics)

    errors = []
    if not valid_subjects:
        errors.append(err_subjects)
    if not valid_date:
        errors.append(err_date)
    if not valid_hours:
        errors.append(err_hours)
    if not valid_topics:
        errors.append(err_topics)

    if errors:
        for err in errors:
            with right_col:
                render_error(err)
        st.session_state["schedule_generated"] = False
    else:
        # Build the plan
        schedule = build_daily_schedule(
            subjects=subjects,
            difficulties=difficulties,
            exam_date=exam_date,
            daily_hours=daily_hours,
            style=style,
            include_recovery=include_recovery,
            topics=topics if topics else None,
        )

        total_study_hours = daily_hours * max(days_remaining(exam_date) - 1, 1)
        allocation = allocate_hours(subjects, difficulties, total_study_hours)

        markdown_export = build_markdown_export(
            subjects=subjects,
            difficulties=difficulties,
            exam_date=exam_date,
            daily_hours=daily_hours,
            style=style,
            include_recovery=include_recovery,
            include_tips=include_tips,
            schedule=schedule,
            allocation=allocation,
            topics=topics if topics else None,
        )

        # Persist in session state
        st.session_state.update({
            "schedule_generated": True,
            "schedule": schedule,
            "subjects": subjects,
            "difficulties": difficulties,
            "exam_date": exam_date,
            "daily_hours": daily_hours,
            "style": style,
            "include_recovery": include_recovery,
            "include_tips": include_tips,
            "allocation": allocation,
            "markdown_export": markdown_export,
            "completed_days": set(),
            "topics": topics,
        })

# ══════════════════════════════════════════════════════════════════════════════
#  RIGHT COLUMN — Output (Tabbed Layout)
# ══════════════════════════════════════════════════════════════════════════════

with right_col:
    if not st.session_state["schedule_generated"]:
        st.markdown("## 👈 Fill in your details to get started")
        st.markdown("""
        <div style="color:#888; font-size:0.95rem; line-height:1.8;">
        ✅ Enter your subjects and difficulty levels<br>
        ✅ Optionally add topics/chapters per subject<br>
        ✅ Set your exam date and daily study hours<br>
        ✅ Choose a study style that suits you<br>
        ✅ Click <strong>Generate My Study Plan</strong>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 💡 Study Style Guide")
        for style_name, profile in STYLE_PROFILES.items():
            st.markdown(f"**{style_name}** — {profile['description']}")

    else:
        sched = st.session_state["schedule"]
        alloc = st.session_state["allocation"]
        subj = st.session_state["subjects"]
        d_hours = st.session_state["daily_hours"]
        ex_date = st.session_state["exam_date"]
        s_style = st.session_state["style"]
        inc_tips = st.session_state["include_tips"]
        md_export = st.session_state["markdown_export"]
        completed = st.session_state["completed_days"]

        st.markdown("## 📋 Your Personalised Study Plan")

        # Urgency banner
        days_left = days_remaining(ex_date)
        urgency = get_urgency_level(days_left)
        if urgency == "critical":
            st.error(f"🔴 Only **{days_left} day(s)** until your exam — focus mode activated!")
        elif urgency == "urgent":
            st.warning(f"🟠 **{days_left} days** left — stay disciplined and keep the pace!")
        elif urgency == "moderate":
            st.info(f"🟡 **{days_left} days** remaining — good time to build momentum.")
        else:
            st.success(f"🟢 **{days_left} days** to go — great head start, pace yourself!")

        # Summary metrics
        render_summary_cards(sched, d_hours, ex_date)

        st.divider()

        # ── Tabbed layout ─────────────────────────────────────────────────
        tab_schedule, tab_analytics, tab_pomodoro = st.tabs([
            "📋 Schedule", "📊 Analytics", "⏱️ Pomodoro Timer"
        ])

        # ── TAB 1: Schedule ───────────────────────────────────────────────
        with tab_schedule:
            # Chart
            render_allocation_chart(subj, alloc)

            st.divider()

            # Progress tracker
            render_progress_tracker(sched)

            st.divider()

            # Daily schedule with checklist
            render_daily_schedule(sched, s_style, inc_tips)

            st.divider()

            # Download buttons
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                render_download_button(md_export, ex_date)
            with dl_col2:
                render_calendar_download(sched, s_style, ex_date)

            st.caption("*Tip: Import the .ics file into Google Calendar, Outlook, or Apple Calendar.*")

        # ── TAB 2: Analytics ──────────────────────────────────────────────
        with tab_analytics:
            render_analytics_dashboard(subj, alloc, sched, completed)

        # ── TAB 3: Pomodoro Timer ─────────────────────────────────────────
        with tab_pomodoro:
            st.markdown("### ⏱️ Focus Timer")
            st.caption("Start a Pomodoro or Deep Work session. Timer runs in your browser.")
            render_pomodoro_timer()

        # ── Auto-save progress ────────────────────────────────────────────
        if st.session_state.get("schedule_generated"):
            try:
                keys_to_save = [
                    "schedule_generated", "schedule", "subjects",
                    "difficulties", "exam_date", "daily_hours",
                    "style", "include_recovery", "include_tips",
                    "allocation", "markdown_export", "completed_days",
                    "topics",
                ]
                auto_state = {k: st.session_state[k] for k in keys_to_save if k in st.session_state}
                auto_save_progress(auto_state)
            except Exception:
                pass  # Silently fail auto-save to not disrupt the UI
