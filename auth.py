import sqlite3
import hashlib

def create_users_table():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(email, password, role):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email, hash_password(password), role)
    )

    conn.commit()
    conn.close()


def verify_user(email, password):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, role, password FROM users WHERE email = ?",
        (email,)
    )

    row = cursor.fetchone()
    conn.close()

    if row and row[3] == hash_password(password):
        return {"id": row[0], "email": row[1], "role": row[2]}

    return None
