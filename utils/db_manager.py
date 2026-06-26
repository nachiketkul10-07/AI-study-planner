"""
db_manager.py — SQLite Database and Authentication Manager for AI Study Planner.
Handles secure user accounts, passwords hashing, and persistent storage of plans.
"""

import sqlite3
import hashlib
import os
import json
from pathlib import Path
from datetime import datetime

# Database file location in the root directory of the workspace
DB_PATH = Path(__file__).resolve().parent.parent / "study_planner.db"


def get_connection():
    """Return a database connection with WAL mode and row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        # 1. Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Plans table (scoped to users)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan_data TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, plan_name)
            );
        """)

        # 3. Autosave table (latest progress per user)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS autosave (
                user_id INTEGER PRIMARY KEY,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan_data TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()


# ── Password Hashing Helpers ──────────────────────────────────────────────────

def _hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    """Hash password with PBKDF2 using SHA-256 and a 16-byte random salt."""
    if salt is None:
        salt = os.urandom(16)
    # Using 100,000 iterations for secure hashing
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex(), salt.hex()


def _verify_password(password: str, stored_hash: str, stored_salt_hex: str) -> bool:
    """Verify input password against stored hash using the user's salt."""
    try:
        salt = bytes.fromhex(stored_salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == stored_hash
    except Exception:
        return False


# ── User authentication operations ─────────────────────────────────────────────

def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    Register a new user in the database.
    Returns (success, message).
    """
    username = username.strip()
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    pwd_hash, salt = _hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?);",
                (username, pwd_hash, salt)
            )
            conn.commit()
        return True, "Registration successful! You can now log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another one."
    except Exception as e:
        return False, f"Database error during registration: {e}"


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate a user.
    Returns a dict with user 'id' and 'username' if successful, else None.
    """
    username = username.strip()
    if not username or not password:
        return None

    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt FROM users WHERE username = ?;",
                (username,)
            ).fetchone()
            
            if row and _verify_password(password, row["password_hash"], row["salt"]):
                return {"id": row["id"], "username": row["username"]}
    except Exception:
        pass
    return None


# ── Plan management operations ────────────────────────────────────────────────

def save_user_plan(user_id: int, plan_name: str, plan_data: dict) -> bool:
    """
    Save or update a study plan under a user account.
    Returns True if saved successfully.
    """
    plan_name = plan_name.strip()
    if not plan_name:
        return False

    plan_json = json.dumps(plan_data)
    timestamp = datetime.now().isoformat()

    try:
        with get_connection() as conn:
            # Check if plan with name exists for this user to update or insert
            conn.execute("""
                INSERT INTO plans (user_id, plan_name, saved_at, plan_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, plan_name) 
                DO UPDATE SET saved_at = excluded.saved_at, plan_data = excluded.plan_data;
            """, (user_id, plan_name, timestamp, plan_json))
            conn.commit()
        return True
    except Exception:
        return False


def load_user_plan(user_id: int, plan_name: str) -> dict | None:
    """
    Load a study plan by name for a user.
    Returns plan data dict or None.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT plan_data FROM plans WHERE user_id = ? AND plan_name = ?;",
                (user_id, plan_name)
            ).fetchone()
            if row:
                return json.loads(row["plan_data"])
    except Exception:
        pass
    return None


def list_user_plans(user_id: int) -> list[dict]:
    """
    List all saved plans for a user.
    Returns list of dicts with 'plan_name' and 'saved_at'.
    """
    plans = []
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT plan_name, saved_at FROM plans WHERE user_id = ? ORDER BY saved_at DESC;",
                (user_id,)
            )
            for row in cursor.fetchall():
                plans.append({
                    "plan_name": row["plan_name"],
                    "saved_at": row["saved_at"]
                })
    except Exception:
        pass
    return plans


def delete_user_plan(user_id: int, plan_name: str) -> bool:
    """
    Delete a plan by name for a user.
    Returns True if deleted successfully.
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM plans WHERE user_id = ? AND plan_name = ?;",
                (user_id, plan_name)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


# ── Autosave operations ───────────────────────────────────────────────────────

def save_user_autosave(user_id: int, plan_data: dict) -> bool:
    """
    Save the current user progress to the autosave table.
    """
    plan_json = json.dumps(plan_data)
    timestamp = datetime.now().isoformat()

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO autosave (user_id, saved_at, plan_data)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) 
                DO UPDATE SET saved_at = excluded.saved_at, plan_data = excluded.plan_data;
            """, (user_id, timestamp, plan_json))
            conn.commit()
        return True
    except Exception:
        return False


def load_user_autosave(user_id: int) -> dict | None:
    """
    Load the autosaved progress for a user.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT plan_data FROM autosave WHERE user_id = ?;",
                (user_id,)
            ).fetchone()
            if row:
                return json.loads(row["plan_data"])
    except Exception:
        pass
    return None
