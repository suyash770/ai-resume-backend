import sqlite3

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        score INTEGER,
        matched TEXT,
        missing TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_candidate(name, score, matched, missing):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO candidates (name, score, matched, missing)
    VALUES (?, ?, ?, ?)
    """, (name, score, ", ".join(matched), ", ".join(missing)))

    conn.commit()
    conn.close()


def get_all_candidates():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, score, matched, missing FROM candidates ORDER BY score DESC")
    rows = cursor.fetchall()
    conn.close()

    return rows
