import sqlite3

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        user_id INTEGER,
        session_id TEXT,
        name TEXT,
        score INTEGER,
        matched TEXT,
        missing TEXT,
        explanation TEXT
    )
    """)

    # Check if session_id column exists
    cursor.execute("PRAGMA table_info(candidates)")
    columns = [col[1] for col in cursor.fetchall()]

    if "session_id" not in columns:
        cursor.execute("ALTER TABLE candidates ADD COLUMN session_id TEXT")

    conn.commit()
    conn.close()


def insert_many(candidates):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?)",
        candidates
    )

    conn.commit()
    conn.close()


def get_candidates_by_user(user_id):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM candidates WHERE user_id = ? ORDER BY score DESC",
        (user_id,)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows
