import sqlite3

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
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
        "INSERT INTO candidates VALUES (?, ?, ?, ?, ?)",
        candidates
    )

    conn.commit()
    conn.close()


def get_all_candidates():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates ORDER BY score DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows


def clear_candidates():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    conn.commit()
    conn.close()
