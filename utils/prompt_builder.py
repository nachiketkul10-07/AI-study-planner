"""
prompt_builder.py — Study plan generation logic (no AI/API required)
"""

from datetime import date, timedelta
from utils.validators import days_remaining, get_urgency_level


# ── Motivational tip bank ─────────────────────────────────────────────────────

MOTIVATIONAL_TIPS = [
    "🌟 Consistency beats intensity. Show up every day, even for 20 minutes.",
    "🧠 Use active recall: quiz yourself instead of re-reading notes.",
    "⏰ The Pomodoro Technique (25 min study + 5 min break) boosts focus.",
    "💤 Sleep consolidates memory. Don't sacrifice sleep for extra study hours.",
    "🎯 Set a clear goal for each session before you start.",
    "📵 Put your phone in another room during study blocks.",
    "🚶 A 10-minute walk before studying can improve focus by up to 20%.",
    "📝 Teach the concept to an imaginary student — if you can explain it, you know it.",
    "🥗 Eat brain-friendly foods: nuts, blueberries, dark chocolate, eggs.",
    "🔁 Spaced repetition: review yesterday's material before starting new content.",
    "📅 Plan your week on Sunday so you never wonder 'what should I study today?'",
    "🏆 Celebrate small wins — finishing a chapter is worth acknowledging!",
    "🌊 Flow state takes ~15 min to enter. Don't break it for trivial distractions.",
    "🤝 Study groups work best for discussion, solo study best for memorisation.",
    "📊 Exam papers from previous years are the single best revision tool.",
]

STYLE_PROFILES = {
    "Balanced": {
        "description": "Steady, even distribution across all days with consistent pacing.",
        "weekend_multiplier": 1.2,
        "session_label": "📚 Study Session",
        "break_note": "Take a 10-min break after every 50 minutes.",
    },
    "Intensive": {
        "description": "Heavy focus in the first half; lighter review closer to the exam.",
        "weekend_multiplier": 1.5,
        "session_label": "🔥 Intensive Block",
        "break_note": "Short breaks (5 min) — maintain high energy and focus.",
    },
    "Slow and Steady": {
        "description": "Gentle ramp-up with extra buffer days and more breaks.",
        "weekend_multiplier": 1.0,
        "session_label": "🐢 Steady Session",
        "break_note": "Rest 15 minutes after each hour — quality over speed.",
    },
    "Night Owl": {
        "description": "Evening-focused sessions; lighter mornings for review.",
        "weekend_multiplier": 1.3,
        "session_label": "🦉 Evening Block",
        "break_note": "Start sessions after 6 PM. Keep a study lamp on to stay alert.",
    },
}


# ── Hour allocation logic ─────────────────────────────────────────────────────

def allocate_hours(
    subjects: list[str],
    difficulties: dict[str, int],
    total_hours: float,
) -> dict[str, float]:
    """
    Distribute total study hours among subjects weighted by difficulty.
    Returns {subject: allocated_hours}.
    """
    total_weight = sum(difficulties[s] for s in subjects)
    allocation = {}
    for subject in subjects:
        proportion = difficulties[subject] / total_weight
        allocation[subject] = round(total_hours * proportion, 1)
    return allocation


def apply_style_weights(
    days: int,
    daily_hours: float,
    style: str,
) -> list[float]:
    """
    Generate a list of daily hour targets based on study style.
    """
    if days <= 0:
        return []

    profile = STYLE_PROFILES[style]
    wm = profile["weekend_multiplier"]
    hours_per_day = []

    for day_index in range(days):
        exam_day = date.today() + timedelta(days=day_index)
        is_weekend = exam_day.weekday() >= 5  # Sat=5, Sun=6
        base = daily_hours * (wm if is_weekend else 1.0)

        if style == "Intensive":
            # Front-load: first half is heavier
            midpoint = days / 2
            if day_index < midpoint:
                multiplier = 1.2
            else:
                multiplier = 0.8
            base *= multiplier

        elif style == "Slow and Steady":
            # Gradual ramp up then plateau
            ramp_fraction = min(day_index / max(days * 0.4, 1), 1.0)
            base *= (0.7 + 0.3 * ramp_fraction)

        elif style == "Night Owl":
            # Steady but slightly increasing toward end
            fraction = day_index / max(days - 1, 1)
            base *= (0.9 + 0.2 * fraction)

        hours_per_day.append(round(min(base, 12), 1))  # cap at 12 hrs/day

    return hours_per_day


# ── Schedule builder ──────────────────────────────────────────────────────────

def build_daily_schedule(
    subjects: list[str],
    difficulties: dict[str, int],
    exam_date: date,
    daily_hours: float,
    style: str,
    include_recovery: bool,
    topics: dict[str, list[str]] | None = None,
) -> list[dict]:
    """
    Build a full daily schedule list.
    Each entry: {date, day_label, hours, tasks: [{subject, duration_min, topic?}], is_recovery}
    Topics cycle through days for each subject.
    """
    days = days_remaining(exam_date)

    # Reserve last day as exam day (light review only)
    study_days = max(days - 1, 1)

    # Optionally add a recovery buffer day every 6 days
    schedule = []
    total_subject_hours = allocate_hours(subjects, difficulties, daily_hours * study_days)
    hourly_weights = apply_style_weights(study_days, daily_hours, style)

    total_weight = sum(hourly_weights) or 1
    subject_pool = {s: total_subject_hours[s] * 60 for s in subjects}  # convert to minutes

    day_cursor = date.today()
    recovery_counter = 0

    for i in range(study_days):
        actual_date = day_cursor + timedelta(days=i)
        day_hours = hourly_weights[i] if i < len(hourly_weights) else daily_hours
        day_minutes = day_hours * 60

        is_recovery = False
        tasks = []

        if include_recovery and recovery_counter == 6:
            # Insert a recovery / buffer day
            is_recovery = True
            recovery_counter = 0
            tasks = [{"subject": "🔄 Recovery & Review", "duration_min": int(day_minutes * 0.5)}]
        else:
            recovery_counter += 1
            # Allocate subjects for the day proportionally
            remaining_minutes = day_minutes
            day_tasks = []

            for j, subject in enumerate(subjects):
                if remaining_minutes <= 0:
                    break
                # Give proportional time relative to difficulty
                diff_weight = difficulties[subject] / sum(difficulties[s] for s in subjects)
                alloc = round(day_minutes * diff_weight)
                alloc = min(alloc, remaining_minutes)
                if alloc >= 10:
                    task_entry = {"subject": subject, "duration_min": int(alloc)}
                    # Cycle through topics if available
                    if topics and topics.get(subject):
                        topic_list = topics[subject]
                        topic_idx = i % len(topic_list)
                        task_entry["topic"] = topic_list[topic_idx]
                    day_tasks.append(task_entry)
                    remaining_minutes -= alloc

            tasks = day_tasks

        day_label = actual_date.strftime("%A, %d %b %Y")
        urgency = get_urgency_level((exam_date - actual_date).days)

        schedule.append({
            "date": actual_date,
            "day_label": day_label,
            "hours": day_hours,
            "tasks": tasks,
            "is_recovery": is_recovery,
            "urgency": urgency,
            "day_number": i + 1,
        })

    # Add exam day
    exam_day_label = exam_date.strftime("%A, %d %b %Y")
    schedule.append({
        "date": exam_date,
        "day_label": exam_day_label,
        "hours": 1.0,
        "tasks": [{"subject": "📋 Light Review + Rest", "duration_min": 60}],
        "is_recovery": False,
        "urgency": "critical",
        "day_number": study_days + 1,
        "is_exam_day": True,
    })

    return schedule


# ── Markdown export builder ───────────────────────────────────────────────────

def build_markdown_export(
    subjects: list[str],
    difficulties: dict[str, int],
    exam_date: date,
    daily_hours: float,
    style: str,
    include_recovery: bool,
    include_tips: bool,
    schedule: list[dict],
    allocation: dict[str, float],
    topics: dict[str, list[str]] | None = None,
) -> str:
    """Generate a full Markdown export of the study plan."""
    lines = []
    lines.append("# 📚 AI Study Planner — Your Personalised Study Plan\n")
    lines.append(f"**Generated on:** {date.today().strftime('%d %B %Y')}  ")
    lines.append(f"**Exam Date:** {exam_date.strftime('%d %B %Y')}  ")
    lines.append(f"**Days Remaining:** {days_remaining(exam_date)}  ")
    lines.append(f"**Study Style:** {style}  ")
    lines.append(f"**Daily Study Hours:** {daily_hours} hrs  \n")

    lines.append("---\n")
    lines.append("## 🎯 Subjects & Difficulty\n")
    lines.append("| Subject | Difficulty | Allocated Hours |")
    lines.append("|---------|------------|-----------------|")
    for s in subjects:
        stars = "⭐" * difficulties[s]
        lines.append(f"| {s} | {stars} ({difficulties[s]}/5) | {allocation[s]} hrs |")

    lines.append("\n---\n")
    lines.append("## 🗓️ Daily Schedule\n")

    for day in schedule:
        is_exam = day.get("is_exam_day", False)
        prefix = "🎓 **EXAM DAY**" if is_exam else f"**Day {day['day_number']}**"
        lines.append(f"### {prefix} — {day['day_label']}")
        if day["is_recovery"]:
            lines.append("> 🔄 Recovery & Buffer Day")
        lines.append(f"- **Study Hours:** {day['hours']} hrs")
        lines.append("- **Tasks:**")
        for task in day["tasks"]:
            topic_str = f" ({task['topic']})" if task.get('topic') else ""
            lines.append(f"  - [ ] {task['subject']}{topic_str} — {task['duration_min']} min")
        lines.append("")

    if include_tips:
        lines.append("---\n")
        lines.append("## 💡 Motivational Tips\n")
        for tip in MOTIVATIONAL_TIPS:
            lines.append(f"- {tip}")

    lines.append("\n---\n")
    lines.append("*Generated by AI Study Planner — Stay focused and you've got this! 🚀*")

    return "\n".join(lines)


# ── Summary stats ─────────────────────────────────────────────────────────────

def compute_summary(
    schedule: list[dict],
    daily_hours: float,
    exam_date: date,
) -> dict:
    """Compute summary statistics for the sidebar / overview."""
    study_days = [d for d in schedule if not d.get("is_exam_day")]
    total_hours = sum(d["hours"] for d in study_days)
    recovery_days = sum(1 for d in study_days if d["is_recovery"])

    return {
        "total_days": days_remaining(exam_date),
        "study_days": len(study_days),
        "recovery_days": recovery_days,
        "total_hours": round(total_hours, 1),
        "avg_daily_hours": round(total_hours / max(len(study_days), 1), 1),
    }
