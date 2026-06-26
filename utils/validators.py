"""
validators.py — Input validation utilities for AI Study Planner
"""

from datetime import date, datetime
from typing import Optional


def parse_subjects(raw_input: str) -> list[str]:
    """
    Parse and clean comma-separated subject input.
    Returns a list of non-empty, stripped subject names.
    """
    if not raw_input or not raw_input.strip():
        return []
    subjects = [s.strip() for s in raw_input.split(",")]
    return [s for s in subjects if s]


def validate_subjects(subjects: list[str]) -> tuple[bool, str]:
    """
    Validate that subjects list is non-empty and has reasonable entries.
    Returns (is_valid, error_message).
    """
    if not subjects:
        return False, "⚠️ Please enter at least one subject."
    if len(subjects) > 15:
        return False, "⚠️ Please limit to 15 subjects for a manageable plan."
    for s in subjects:
        if len(s) > 60:
            return False, f"⚠️ Subject name too long: '{s[:30]}...'. Keep it under 60 characters."
    return True, ""


def validate_exam_date(exam_date: date) -> tuple[bool, str]:
    """
    Validate that the exam date is in the future.
    Returns (is_valid, error_message).
    """
    today = date.today()
    if exam_date <= today:
        return False, "⚠️ Exam date must be in the future. Please select a future date."
    days_remaining = (exam_date - today).days
    if days_remaining > 365:
        return False, "⚠️ Exam date is more than a year away. Please double-check your date."
    return True, ""


def validate_study_hours(hours: float) -> tuple[bool, str]:
    """
    Validate daily study hours is within a reasonable range.
    """
    if hours <= 0:
        return False, "⚠️ Daily study hours must be greater than 0."
    if hours > 16:
        return False, "⚠️ More than 16 hours/day is unrealistic. Please enter a healthy value."
    return True, ""


def days_remaining(exam_date: date) -> int:
    """Return the number of days from today until the exam date."""
    return (exam_date - date.today()).days


def get_urgency_level(days: int) -> str:
    """Classify urgency based on days remaining."""
    if days <= 3:
        return "critical"
    elif days <= 7:
        return "urgent"
    elif days <= 14:
        return "moderate"
    else:
        return "relaxed"


def parse_topics(raw_input: str) -> list[str]:
    """
    Parse and clean comma-separated topic input for a subject.
    Returns a list of non-empty, stripped topic names.
    """
    if not raw_input or not raw_input.strip():
        return []
    topics = [t.strip() for t in raw_input.split(",")]
    return [t for t in topics if t]


def validate_topics(topics: dict[str, list[str]]) -> tuple[bool, str]:
    """
    Validate the topics dict {subject: [topic_list]}.
    Returns (is_valid, error_message).
    """
    for subject, topic_list in topics.items():
        if len(topic_list) > 20:
            return False, f"⚠️ Too many topics for {subject}. Please limit to 20."
        for t in topic_list:
            if len(t) > 80:
                return False, f"⚠️ Topic name too long in {subject}: '{t[:30]}...'"
    return True, ""
