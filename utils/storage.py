"""
storage.py — Database & File Save/Load Plan Bridge for AI Study Planner.
Integrates user login and SQLite database storage, with local file storage fallback.
"""

import json
import os
import re
import streamlit as st
from datetime import date, datetime
from pathlib import Path

# Import database manager functions
from utils.db_manager import (
    init_db,
    register_user,
    authenticate_user,
    save_user_plan,
    load_user_plan,
    list_user_plans,
    delete_user_plan,
    save_user_autosave,
    load_user_autosave,
)

# Initialise database tables
init_db()

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


# ── Local File Operations (Fallback for guest users) ──────────────────────────

def _ensure_dir():
    """Create the save directory if it doesn't exist."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def _sanitise_filename(name: str) -> str:
    """Sanitise a plan name for use as a filename."""
    clean = re.sub(r"[^\w\s-]", "", name.strip())
    clean = re.sub(r"[\s]+", "_", clean)
    return clean[:60] or "untitled"


# ── Unified Core Operations (Database-first, File-fallback) ───────────────────

def save_plan(name: str, state_data: dict) -> str:
    """
    Save a study plan to database (if logged in) or file (if guest).
    """
    user = st.session_state.get("logged_in_user")
    
    # Custom encoding to ensure dates/sets are serialisable
    serialised_data = json.loads(json.dumps(state_data, cls=StudyPlanEncoder))

    if user:
        # Save to database
        success = save_user_plan(user["id"], name, serialised_data)
        if success:
            return f"Database: {name}"
        raise IOError("Failed to save plan to database.")
    else:
        # Fallback to local files
        _ensure_dir()
        safe_name = _sanitise_filename(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"
        filepath = SAVE_DIR / filename

        payload = {
            "plan_name": name,
            "saved_at": datetime.now().isoformat(),
            "data": serialised_data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return filename


def load_plan(plan_identifier: str) -> dict | None:
    """
    Load a study plan by name (database) or filename (fallback files).
    """
    user = st.session_state.get("logged_in_user")
    
    if user:
        # Load from database
        data = load_user_plan(user["id"], plan_identifier)
        if data:
            # Decode to restore date and set objects
            return {"data": json.loads(json.dumps(data), object_hook=_decode_hook)}
        return None
    else:
        # Load from file
        filepath = SAVE_DIR / plan_identifier
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f, object_hook=_decode_hook)


def list_saved_plans() -> list[dict]:
    """
    List all saved plans from database (if logged in) or files (if guest).
    """
    user = st.session_state.get("logged_in_user")

    if user:
        db_plans = list_user_plans(user["id"])
        # Format to match expectations
        return [
            {
                "filename": p["plan_name"],
                "plan_name": p["plan_name"],
                "saved_at": p["saved_at"],
            }
            for p in db_plans
        ]
    else:
        _ensure_dir()
        plans = []
        for filepath in sorted(SAVE_DIR.glob("*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                plans.append({
                    "filename": filepath.name,
                    "plan_name": data.get("plan_name", filepath.name),
                    "saved_at": data.get("saved_at", "Unknown"),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return plans


def delete_plan(plan_identifier: str) -> bool:
    """Delete a plan by database name or file path."""
    user = st.session_state.get("logged_in_user")

    if user:
        return delete_user_plan(user["id"], plan_identifier)
    else:
        filepath = SAVE_DIR / plan_identifier
        if filepath.exists():
            filepath.unlink()
            return True
        return False


def auto_save_progress(state_data: dict):
    """
    Auto-save progress to database (logged-in) or file (guest).
    """
    user = st.session_state.get("logged_in_user")
    serialised_data = json.loads(json.dumps(state_data, cls=StudyPlanEncoder))

    if user:
        save_user_autosave(user["id"], serialised_data)
    else:
        _ensure_dir()
        filepath = SAVE_DIR / "_autosave_progress.json"
        payload = {
            "plan_name": "Auto-Save",
            "saved_at": datetime.now().isoformat(),
            "data": serialised_data,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


def load_autosave() -> dict | None:
    """Load user's autosave from database (if logged-in) or file (if guest)."""
    user = st.session_state.get("logged_in_user")

    if user:
        data = load_user_autosave(user["id"])
        if data:
            return {"data": json.loads(json.dumps(data), object_hook=_decode_hook)}
        return None
    else:
        filepath = SAVE_DIR / "_autosave_progress.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f, object_hook=_decode_hook)
        except (json.JSONDecodeError, KeyError):
            return None


# ── Sidebar UI with Registration & Login ─────────────────────────────────────

def render_save_load_sidebar():
    """Render Login/Sign Up controls or Save/Load database interface in the sidebar."""
    st.sidebar.markdown("## 👤 User Accounts")

    # Check if user is logged in
    user = st.session_state.get("logged_in_user")

    if not user:
        # Tabbed Login / Sign Up UI
        tab_login, tab_signup = st.sidebar.tabs(["🔐 Log In", "📝 Sign Up"])

        with tab_login:
            st.markdown("##### Log In to Your Account")
            login_user = st.text_input("Username", key="login_username_input", placeholder="Enter username")
            login_pass = st.text_input("Password", type="password", key="login_password_input", placeholder="Enter password")
            
            if st.button("Log In", use_container_width=True, key="btn_login"):
                if not login_user.strip() or not login_pass:
                    st.sidebar.error("Please enter both username and password.")
                else:
                    auth_user = authenticate_user(login_user, login_pass)
                    if auth_user:
                        st.session_state["logged_in_user"] = auth_user
                        st.sidebar.success(f"Welcome back, {auth_user['username']}!")
                        
                        # Load user's autosave progress from DB if it exists
                        autosave_data = load_autosave()
                        if autosave_data and "data" in autosave_data:
                            for k, v in autosave_data["data"].items():
                                st.session_state[k] = v
                        
                        st.rerun()
                    else:
                        st.sidebar.error("Invalid username or password.")

        with tab_signup:
            st.markdown("##### Create a New Account")
            reg_user = st.text_input("Username", key="reg_username_input", placeholder="At least 3 characters")
            reg_pass = st.text_input("Password", type="password", key="reg_password_input", placeholder="At least 6 characters")
            reg_pass_conf = st.text_input("Confirm Password", type="password", key="reg_password_conf_input", placeholder="Repeat password")
            
            if st.button("Register Account", use_container_width=True, key="btn_register"):
                if reg_pass != reg_pass_conf:
                    st.sidebar.error("Passwords do not match.")
                else:
                    success, msg = register_user(reg_user, reg_pass)
                    if success:
                        st.sidebar.success(msg)
                    else:
                        st.sidebar.error(msg)
        
        st.sidebar.divider()
        st.sidebar.info("💡 Logging in allows you to save and load plans securely to a persistent database.")

    else:
        # Logged-in view
        st.sidebar.markdown(f"Logged in as: **{user['username']}**")
        if st.sidebar.button("🚪 Log Out", use_container_width=True, key="btn_logout"):
            # Clear user session and reset generated states
            st.session_state["logged_in_user"] = None
            st.session_state["schedule_generated"] = False
            # Clear all study plan data from state to prevent showing other user's plans
            defaults = {
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
            for key, val in defaults.items():
                st.session_state[key] = val
            st.sidebar.success("Logged out successfully.")
            st.rerun()

        st.sidebar.divider()
        st.sidebar.markdown("### 💾 Saved Plans (Database)")
        
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

                try:
                    filename = save_plan(plan_name, state)
                    st.sidebar.success(f"✅ Saved plan successfully!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Save failed: {e}")

        st.sidebar.divider()

        # ── Load section ──────────────────────────────────────────────────────
        st.sidebar.markdown("#### Load Saved Plan")
        plans = list_saved_plans()

        if not plans:
            st.sidebar.caption("No saved plans in database yet.")
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
                    if delete_plan(selected):
                        st.sidebar.success("🗑️ Deleted.")
                        st.rerun()
                    else:
                        st.sidebar.error("Failed to delete plan.")
