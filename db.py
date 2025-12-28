import sqlite3
import hashlib
from datetime import date, datetime

DB_NAME = "planner.db"


def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_db()

    # ------ USERS ------
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        branch TEXT,
        phone TEXT,
        dob TEXT,
        photo_path TEXT
    )
    """)

    # MIGRATION (adds new fields if DB existed earlier)
    try: conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except: pass

    try: conn.execute("ALTER TABLE users ADD COLUMN dob TEXT")
    except: pass

    try: conn.execute("ALTER TABLE users ADD COLUMN photo_path TEXT")
    except: pass

    # ------ TASKS ------
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        deadline TEXT,
        assigned_to TEXT,
        created_by INTEGER,
        pdf_path TEXT
    )
    """)

    # ------ COMPLETED ------
    conn.execute("""
    CREATE TABLE IF NOT EXISTS completed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        task_id INTEGER
    )
    """)

    # ------ ATTENDANCE ------
    conn.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT
    )
    """)

    # ------ LIBRARY ------
    conn.execute("""
    CREATE TABLE IF NOT EXISTS library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        file_path TEXT,
        uploaded_by INTEGER,
        branch TEXT,
        uploaded_at TEXT
    )
    """)

    # Library migrations (for older DBs)
    try: conn.execute("ALTER TABLE library ADD COLUMN branch TEXT")
    except: pass

    try: conn.execute("ALTER TABLE library ADD COLUMN uploaded_at TEXT")
    except: pass

    conn.commit()


# -------- USERS --------
def get_user(email, password):
    conn = get_db()
    pw = hash_password(password)
    row = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, pw)
    ).fetchone()
    return dict(row) if row else None


def get_all_users():
    conn = get_db()
    return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]


# -------- TASKS --------
def add_task(title, desc, deadline, assigned_to, teacher_id):
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (title,description,deadline,assigned_to,created_by) VALUES (?,?,?,?,?)",
        (title, desc, deadline, assigned_to, teacher_id)
    )
    conn.commit()


def get_tasks():
    conn = get_db()
    return [dict(r) for r in conn.execute("SELECT * FROM tasks").fetchall()]


def update_task(task_id, title, desc, deadline):
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET title=?, description=?, deadline=? WHERE id=?",
        (title, desc, deadline, task_id)
    )
    conn.commit()


def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()


def mark_completed(student_id, task_id):
    conn = get_db()
    conn.execute(
        "INSERT INTO completed (student_id, task_id) VALUES (?,?)",
        (student_id, task_id)
    )
    conn.commit()


# -------- ATTENDANCE --------
def mark_attendance(student_id):
    conn = get_db()
    today = date.today().isoformat()

    exists = conn.execute(
        "SELECT 1 FROM attendance WHERE student_id=? AND date=?",
        (student_id, today)
    ).fetchone()

    if not exists:
        conn.execute(
            "INSERT INTO attendance (student_id, date) VALUES (?,?)",
            (student_id, today)
        )
        conn.commit()


def get_attendance(student_id):
    conn = get_db()
    return [dict(r) for r in conn.execute(
        "SELECT * FROM attendance WHERE student_id=?",
        (student_id,)
    ).fetchall()]


def get_attendance_report():
    conn = get_db()
    return [dict(r) for r in conn.execute("""
        SELECT u.name, u.branch, COUNT(a.id) AS attended_days
        FROM users u
        LEFT JOIN attendance a ON u.id = a.student_id
        WHERE u.role='student'
        GROUP BY u.id
    """).fetchall()]


# -------- PERFORMANCE --------
def get_performance():
    conn = get_db()
    return [dict(r) for r in conn.execute("""
        SELECT u.name, u.branch, COUNT(c.id) AS completed_tasks
        FROM users u
        LEFT JOIN completed c ON u.id = c.student_id
        WHERE u.role='student'
        GROUP BY u.id
    """).fetchall()]


# -------- LIBRARY --------
def add_library_item(title, description, file_path, uploaded_by, branch):
    conn = get_db()
    conn.execute(
        "INSERT INTO library (title, description, file_path, uploaded_by, branch, uploaded_at) VALUES (?,?,?,?,?,?)",
        (title, description, file_path, uploaded_by, branch, datetime.now().isoformat())
    )
    conn.commit()


def get_library_items(branch=None):
    conn = get_db()
    if branch:
        rows = conn.execute(
            "SELECT * FROM library WHERE branch=? OR branch='ALL' ORDER BY id DESC",
            (branch,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM library ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def delete_library_item(lib_id):
    conn = get_db()
    conn.execute("DELETE FROM library WHERE id=?", (lib_id,))
    conn.commit()


init_db()
