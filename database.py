import sqlite3

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    # Force recreate table with correct schema
    cursor.execute("DROP TABLE IF EXISTS candidates")

    cursor.execute("""
    CREATE TABLE candidates (
        user_id INTEGER,
        session_id TEXT,
        name TEXT,
        score INTEGER,
        matched TEXT,
        missing TEXT,
        explanation TEXT
    )
    """)

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
