"""
calendar_export.py — ICS Calendar Export for AI Study Planner
Generates RFC 5545 compliant .ics files without external libraries.
"""

import streamlit as st
from datetime import datetime, timedelta, timezone
import uuid


def _escape_ics_text(text: str) -> str:
    """Escape special characters for ICS text fields."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold_line(line: str) -> str:
    """
    Fold long lines to comply with RFC 5545 (limit to 75 octets/bytes).
    Each folded line segment starts with a CRLF followed by a single space.
    """
    # Fold at 70 characters to be safely under 75 bytes
    if len(line) <= 70:
        return line
    parts = [line[:70]]
    remaining = line[70:]
    while remaining:
        parts.append(" " + remaining[:69])
        remaining = remaining[69:]
    return "\r\n".join(parts)


def generate_ics_content(
    schedule: list[dict],
    style: str,
    start_hour: int = 9,
) -> str:
    """
    Generate ICS calendar content from a study schedule.

    Args:
        schedule: List of day dicts from build_daily_schedule().
        style: Study style name for event descriptions.
        start_hour: Hour of day to start study sessions (default 9 AM).

    Returns:
        String containing the full ICS file content.
    """
    # dtstamp MUST be in UTC format (with a 'Z') and is required for all VEVENTs
    dtstamp_str = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI Study Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:AI Study Plan",
    ]

    for day in schedule:
        study_date = day["date"]
        is_exam = day.get("is_exam_day", False)
        is_recovery = day.get("is_recovery", False)
        current_hour = start_hour
        current_minute = 0

        for task in day.get("tasks", []):
            subject = task["subject"]
            topic = task.get("topic", "")
            duration_min = task["duration_min"]

            # Build event times (naive local / floating time)
            dt_start = datetime(
                study_date.year, study_date.month, study_date.day,
                current_hour, current_minute
            )
            dt_end = dt_start + timedelta(minutes=duration_min)

            # Advance the clock for the next task
            current_hour = dt_end.hour
            current_minute = dt_end.minute

            # Build summary
            if is_exam:
                summary = f"🎓 Exam Day — {subject}"
            elif is_recovery:
                summary = f"🔄 Recovery — {subject}"
            else:
                summary = f"📚 {subject}"
                if topic:
                    summary += f" — {topic}"

            # Build description
            desc_parts = [
                f"Study Style: {style}",
                f"Duration: {duration_min} min",
                f"Day {day['day_number']} of your study plan",
            ]
            if topic:
                desc_parts.insert(1, f"Topic: {topic}")
            if is_recovery:
                desc_parts.append("Light review and rest day.")
            description = "\\n".join(desc_parts)

            uid = str(uuid.uuid4())

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp_str}",
                f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{_escape_ics_text(summary)}",
                f"DESCRIPTION:{_escape_ics_text(description)}",
                "STATUS:CONFIRMED",
                f"CATEGORIES:{'Exam' if is_exam else 'Study'}",
                "END:VEVENT",
            ])

    lines.append("END:VCALENDAR")
    
    # Fold lines according to RFC 5545 before joining
    folded_lines = [_fold_line(line) for line in lines]
    return "\r\n".join(folded_lines)


def render_calendar_download(schedule: list[dict], style: str, exam_date):
    """Render a download button for the ICS calendar export."""
    ics_content = generate_ics_content(schedule, style)
    filename = f"study_plan_{exam_date.strftime('%Y%m%d')}.ics"

    st.download_button(
        label="📅 Export to Calendar (.ics)",
        data=ics_content.encode("utf-8"),
        file_name=filename,
        mime="text/calendar",
        use_container_width=True,
    )

