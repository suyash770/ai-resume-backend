import sqlite3

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def insert_many(records):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT INTO candidates
        (user_id, session_id, name, score, matched, missing, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()


def get_candidates_by_user(user_id):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM candidates
        WHERE user_id = ?
        ORDER BY rowid DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows
