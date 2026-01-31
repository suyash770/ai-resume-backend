import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

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


def register_user(email, password, role):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    hashed = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email, hashed, role)
    )

    conn.commit()
    conn.close()


def verify_user(email, password):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        return {"id": user[0], "email": user[1], "role": user[3]}
    return None
