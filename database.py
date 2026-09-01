"""
database.py
Handles all SQLite storage for the AI Timetable Planner.

The timetable is the CORE feature (Google Calendar style), so its schema
is the most fleshed-out. Assignments/exams are simple stub tables for
now — Week 2 will expand them.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "timetable.db"

# A small fixed color palette so each subject gets a consistent,
# Google-Calendar-like color block in the UI. Distinct, readable hues.
SUBJECT_COLORS = [
    "#4285F4",  # blue
    "#EA4335",  # red
    "#34A853",  # green
    "#FBBC04",  # yellow
    "#A142F4",  # purple
    "#FF6D01",  # orange
    "#00ACC1",  # cyan
    "#E91E63",  # pink
    "#8D6E63",  # brown
    "#5F6368",  # gray
]


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist yet. Call this once at app startup."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS timetable_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT,
                event_date TEXT NOT NULL,      -- 'YYYY-MM-DD'
                start_time TEXT NOT NULL,      -- 'HH:MM' 24-hour
                end_time TEXT NOT NULL,        -- 'HH:MM' 24-hour
                color TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Remembers which color each subject was assigned, so it never
        # changes even after events are added/edited/deleted.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subject_colors (
                subject TEXT PRIMARY KEY,
                color TEXT NOT NULL
            )
        """)

        # Stub tables for Week 2 — kept minimal for now
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT,
                due_date TEXT,
                progress INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Week 3: onboarding — who the student is, one row (single-user app)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT,
                grade TEXT,
                onboarded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Lightweight migration: add tutorial_seen if it's missing (for
        # anyone who already had a student_profile table before this existed)
        existing_cols = [row["name"] for row in
                          conn.execute("PRAGMA table_info(student_profile)").fetchall()]
        if "tutorial_seen" not in existing_cols:
            conn.execute(
                "ALTER TABLE student_profile ADD COLUMN tutorial_seen INTEGER DEFAULT 0"
            )

        # Week 3: syllabus chapters, so the AI can find "Chapter 3 of
        # Geography" when asked to make a mindmap or quiz
        conn.execute("""
            CREATE TABLE IF NOT EXISTS syllabus_chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                content TEXT NOT NULL,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _color_for_subject(subject: str) -> str:
    """Look up (or assign) a persistent color for a subject. Each new
    subject gets the next unused color from the palette, in order, and
    keeps that color forever — even if you rename other subjects later."""
    if not subject:
        return SUBJECT_COLORS[0]

    with get_conn() as conn:
        row = conn.execute(
            "SELECT color FROM subject_colors WHERE subject = ?", (subject,)
        ).fetchone()
        if row:
            return row["color"]

        count = conn.execute("SELECT COUNT(*) AS n FROM subject_colors").fetchone()["n"]
        color = SUBJECT_COLORS[count % len(SUBJECT_COLORS)]
        conn.execute(
            "INSERT INTO subject_colors (subject, color) VALUES (?, ?)",
            (subject, color),
        )
        return color


# ---------- Timetable CRUD (the core feature) ----------

def add_event(title, subject, event_date, start_time, end_time, notes=""):
    """Add a new timetable event. Dates as 'YYYY-MM-DD', times as 'HH:MM'."""
    color = _color_for_subject(subject)
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO timetable_events
               (title, subject, event_date, start_time, end_time, color, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, subject, event_date, start_time, end_time, color, notes),
        )
        return cur.lastrowid


def update_event(event_id, **fields):
    """Update any subset of fields on an existing event (e.g. new start_time)."""
    if not fields:
        return False
    allowed = {"title", "subject", "event_date", "start_time", "end_time", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False

    if "subject" in updates:
        updates["color"] = _color_for_subject(updates["subject"])

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [event_id]

    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE timetable_events SET {set_clause} WHERE id = ?", values
        )
        return cur.rowcount > 0


def delete_event(event_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM timetable_events WHERE id = ?", (event_id,))
        return cur.rowcount > 0


def find_events(event_date=None, subject=None, title_contains=None):
    """Flexible lookup — used by the AI to find 'the English class on Wednesday'."""
    query = "SELECT * FROM timetable_events WHERE 1=1"
    params = []
    if event_date:
        query += " AND event_date = ?"
        params.append(event_date)
    if subject:
        query += " AND subject LIKE ?"
        params.append(f"%{subject}%")
    if title_contains:
        query += " AND title LIKE ?"
        params.append(f"%{title_contains}%")
    query += " ORDER BY event_date, start_time"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_events_in_range(start_date, end_date):
    """Used by the calendar view to fetch a week's worth of events."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM timetable_events
               WHERE event_date BETWEEN ? AND ?
               ORDER BY event_date, start_time""",
            (start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_events():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM timetable_events ORDER BY event_date, start_time"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Assignment CRUD (Week 2) ----------

def add_assignment(title, subject="", due_date=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO assignments (title, subject, due_date, progress) VALUES (?, ?, ?, 0)",
            (title, subject, due_date),
        )
        return cur.lastrowid


def find_assignments(subject=None, due_before=None, include_completed=True):
    """Look up assignments, optionally filtered by subject or due date.
    Set include_completed=False to only show ones under 100% progress."""
    query = "SELECT * FROM assignments WHERE 1=1"
    params = []
    if subject:
        query += " AND subject LIKE ?"
        params.append(f"%{subject}%")
    if due_before:
        query += " AND due_date <= ?"
        params.append(due_before)
    if not include_completed:
        query += " AND progress < 100"
    query += " ORDER BY due_date"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def update_assignment_progress(assignment_id, progress):
    """progress is an integer 0-100."""
    progress = max(0, min(100, int(progress)))
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE assignments SET progress = ? WHERE id = ?",
            (progress, assignment_id),
        )
        return cur.rowcount > 0


def delete_assignment(assignment_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        return cur.rowcount > 0


def get_subject_color(subject):
    """Public lookup for a subject's assigned color — used anywhere in the
    app (Kanban, To-Do List) that needs to match the Timetable's colors.
    Assigns a new color on first use, same as timetable events do."""
    return _color_for_subject(subject)


def get_due_now(reference_date):
    """Assignments due on or before the given date ('YYYY-MM-DD') that
    aren't finished yet — used for 'what's due right now' style queries."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM assignments
               WHERE due_date <= ? AND progress < 100
               ORDER BY due_date""",
            (reference_date,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Exam CRUD (Week 2) ----------

def add_exam(subject, exam_date, notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO exams (subject, exam_date, notes) VALUES (?, ?, ?)",
            (subject, exam_date, notes),
        )
        return cur.lastrowid


def get_upcoming_exams(reference_date):
    """All exams on or after the given date, soonest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM exams WHERE exam_date >= ? ORDER BY exam_date",
            (reference_date,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Onboarding: student profile + syllabus (Week 3) ----------

def save_student_profile(name, grade):
    """There's only ever one profile row (id=1) — this app is single-user.
    Calling this again just overwrites the existing profile."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO student_profile (id, name, grade)
               VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name = excluded.name, grade = excluded.grade""",
            (name, grade),
        )


def get_student_profile():
    """Returns the profile dict, or None if onboarding hasn't happened yet."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM student_profile WHERE id = 1").fetchone()
        return dict(row) if row else None


def mark_tutorial_seen():
    """Called once the user finishes the tutorial screen, so it doesn't
    show again on their next visit."""
    with get_conn() as conn:
        conn.execute("UPDATE student_profile SET tutorial_seen = 1 WHERE id = 1")


def add_syllabus_chapter(subject, chapter_name, content):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO syllabus_chapters (subject, chapter_name, content)
               VALUES (?, ?, ?)""",
            (subject, chapter_name, content),
        )
        return cur.lastrowid


def add_syllabus_chapters_bulk(subject, chapters):
    """chapters is a list of (chapter_name, content) tuples — used right
    after syllabus_parser.split_into_chapters() so a whole syllabus upload
    becomes many chapter rows in one go, no manual typing needed."""
    with get_conn() as conn:
        for chapter_name, content in chapters:
            conn.execute(
                """INSERT INTO syllabus_chapters (subject, chapter_name, content)
                   VALUES (?, ?, ?)""",
                (subject, chapter_name, content),
            )


def find_syllabus_chapter(subject, chapter_name=None):
    """Flexible lookup — used by the AI to find 'Chapter 3 of Geography'
    even if the user doesn't type the chapter name exactly right."""
    query = "SELECT * FROM syllabus_chapters WHERE subject LIKE ?"
    params = [f"%{subject}%"]
    if chapter_name:
        query += " AND chapter_name LIKE ?"
        params.append(f"%{chapter_name}%")

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_all_syllabus_chapters():
    """Used by the onboarding page to show what's already been added."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, subject, chapter_name, added_at FROM syllabus_chapters "
            "ORDER BY subject, chapter_name"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_syllabus_chapter(chapter_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM syllabus_chapters WHERE id = ?", (chapter_id,))
        return cur.rowcount > 0