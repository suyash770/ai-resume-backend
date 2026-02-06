import os
import re
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Import custom modules
from pdf_reader import extract_text_from_pdf
from nlp_matcher import match_resume_to_jd

app = Flask(__name__)
CORS(app)

DB_PATH = 'ats_database.db'

def init_db():
    """Initializes persistent SQLite tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users Table with unique email constraint
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, email TEXT UNIQUE, mobile TEXT, password TEXT, role TEXT)''')
    # Candidates/Analysis Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, score INTEGER, matched TEXT, 
        missing TEXT, explanation TEXT, timestamp DATETIME)''')
    # Activity Logs Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, action TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['POST'])
def register():
    """Saves new user details to the database"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, email, mobile, password, role) VALUES (?, ?, ?, ?, ?)',
                       (data['name'], data['email'], data['mobile'], data['pass'], data['role']))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists!"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Verifies credentials and returns role-based redirection"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email=? AND password=? AND role=?', 
                   (data['email'], data['pass'], data['role']))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = dict(user)
        # Determine target dashboard based on role
        redirect_page = "admin.html" if user_data['role'] == 'admin' else \
                        "index.html" if user_data['role'] == 'hr' else "candidate.html"
        return jsonify({"user": user_data, "redirect": redirect_page}), 200
    else:
        return jsonify({"error": "Invalid email, password, or role selection!"}), 401

# --- ANALYSIS & LOGGING ROUTES ---

@app.route('/predict', methods=['POST'])
def predict():
    jd_text = request.form.get('jd_text', '')
    hr_email = request.form.get('hr_email', 'system@ats.com')
    if 'jd_pdf' in request.files:
        jd_text = extract_text_from_pdf(request.files['jd_pdf'])
    
    resumes = request.files.getlist('resume_pdfs')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for resume_file in resumes:
        filename = secure_filename(resume_file.filename)
        resume_text = extract_text_from_pdf(resume_file)
        analysis = match_resume_to_jd(resume_text, jd_text)
        
        cursor.execute('INSERT INTO candidates (name, email, score, matched, missing, explanation, timestamp) VALUES (?,?,?,?,?,?,?)',
                       (filename, "extracted@mail.com", analysis['score'], analysis['matched_skills'], 
                        analysis['missing_skills'], analysis['explanation'], datetime.now()))
        cursor.execute('INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)',
                       (hr_email, f"Analyzed: {filename}", datetime.now()))

    conn.commit()
    conn.close()
    return jsonify({"message": "Success"}), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM candidates ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM candidates')
    total_runs = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    conn.close()
    return jsonify({"total_runs": total_runs, "total_users": total_users}), 200

@app.route('/admin/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)