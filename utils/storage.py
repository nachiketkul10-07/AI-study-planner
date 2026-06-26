"""
storage.py — Save & Load Plans for AI Study Planner
Persists study plans as JSON files in a local directory.
"""

import json
import os
import re
import streamlit as st
from datetime import date, datetime
from pathlib import Path


SAVE_DIR = Path(__file__).resolve().parent.parent / "saved_plans"


# ── JSON serialisation helpers ────────────────────────────────────────────────

class StudyPlanEncoder(json.JSONEncoder):
    """Custom encoder that handles date and set objects."""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return {"__type__": "date", "value": obj.isoformat()}
        if isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}
        return super().default(obj)


def _decode_hook(obj: dict):
    """Object hook to restore date and set objects."""
    if "__type__" in obj:
        if obj["__type__"] == "date":
            try:
                return datetime.fromisoformat(obj["value"]).date()
            except (ValueError, TypeError):
                return obj["value"]
        if obj["__type__"] == "set":
            return set(obj["value"])
    return obj


# ── Core operations ───────────────────────────────────────────────────────────

def _ensure_dir():
    """Create the save directory if it doesn't exist."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def _sanitise_filename(name: str) -> str:
    """Sanitise a plan name for use as a filename."""
    clean = re.sub(r"[^\w\s-]", "", name.strip())
    clean = re.sub(r"[\s]+", "_", clean)
    return clean[:60] or "untitled"


def save_plan(name: str, state_data: dict) -> str:
    """
    Save a study plan to a JSON file.

    Args:
        name: Human-readable plan name.
        state_data: Dict of session state keys to persist.

    Returns:
        The filename that was saved.
    """
    _ensure_dir()
    safe_name = _sanitise_filename(name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.json"
    filepath = SAVE_DIR / filename

    payload = {
        "plan_name": name,
        "saved_at": datetime.now().isoformat(),
        "data": state_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, cls=StudyPlanEncoder, indent=2, ensure_ascii=False)

    return filename


def load_plan(filename: str) -> dict | None:
    """
    Load a study plan from a JSON file.

    Returns:
        The full payload dict, or None if file not found.
    """
    filepath = SAVE_DIR / filename
    if not filepath.exists():
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f, object_hook=_decode_hook)


def list_saved_plans() -> list[dict]:
    """
    List all saved plans with metadata.

    Returns:
        List of dicts with 'filename', 'plan_name', 'saved_at'.
    """
    _ensure_dir()
    plans = []
    for filepath in sorted(SAVE_DIR.glob("*.json"), reverse=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            plans.append({
                "filename": filepath.name,
                "plan_name": data.get("plan_name", filepath.stem),
                "saved_at": data.get("saved_at", "Unknown"),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return plans


def delete_plan(filename: str) -> bool:
    """Delete a saved plan file. Returns True if deleted."""
    filepath = SAVE_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def auto_save_progress(state_data: dict):
    """
    Auto-save progress (completed days) to a special file.
    This overwrites the previous auto-save.
    """
    _ensure_dir()
    filepath = SAVE_DIR / "_autosave_progress.json"
    payload = {
        "plan_name": "Auto-Save",
        "saved_at": datetime.now().isoformat(),
        "data": state_data,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, cls=StudyPlanEncoder, indent=2, ensure_ascii=False)


def load_autosave() -> dict | None:
    """Load the auto-saved progress, if it exists."""
    filepath = SAVE_DIR / "_autosave_progress.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f, object_hook=_decode_hook)
    except (json.JSONDecodeError, KeyError):
        return None


# ── Sidebar UI ────────────────────────────────────────────────────────────────

def render_save_load_sidebar():
    """Render the save/load UI in the Streamlit sidebar."""

    st.sidebar.markdown("## 💾 Save & Load")

    # ── Save section ──────────────────────────────────────────────────────
    st.sidebar.markdown("#### Save Current Plan")
    plan_name = st.sidebar.text_input(
        "Plan name",
        placeholder="e.g. Finals Week Plan",
        key="save_plan_name",
    )

    if st.sidebar.button("💾 Save Plan", use_container_width=True, key="btn_save"):
        if not plan_name.strip():
            st.sidebar.error("Please enter a plan name.")
        elif not st.session_state.get("schedule_generated"):
            st.sidebar.warning("Generate a plan first before saving.")
        else:
            # Collect saveable state
            keys_to_save = [
                "schedule_generated", "schedule", "subjects",
                "difficulties", "exam_date", "daily_hours",
                "style", "include_recovery", "include_tips",
                "allocation", "markdown_export", "completed_days",
                "topics",
            ]
            state = {}
            for k in keys_to_save:
                if k in st.session_state:
                    state[k] = st.session_state[k]

            filename = save_plan(plan_name, state)
            st.sidebar.success(f"✅ Saved as `{filename}`")

    st.sidebar.divider()

    # ── Load section ──────────────────────────────────────────────────────
    st.sidebar.markdown("#### Load Saved Plan")
    plans = list_saved_plans()

    if not plans:
        st.sidebar.caption("No saved plans yet.")
    else:
        options = {p["filename"]: f"{p['plan_name']}  •  {p['saved_at'][:10]}" for p in plans}
        selected = st.sidebar.selectbox(
            "Select a plan",
            options=list(options.keys()),
            format_func=lambda x: options[x],
            key="load_plan_select",
        )

        col_load, col_delete = st.sidebar.columns(2)

        with col_load:
            if st.button("📂 Load", use_container_width=True, key="btn_load"):
                payload = load_plan(selected)
                if payload and "data" in payload:
                    for k, v in payload["data"].items():
                        st.session_state[k] = v
                    st.sidebar.success("✅ Plan loaded!")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to load plan.")

        with col_delete:
            if st.button("🗑️ Delete", use_container_width=True, key="btn_delete"):
                delete_plan(selected)
                st.sidebar.success("🗑️ Deleted.")
                st.rerun()
