import os
import re
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Required helper modules (Ensure these exist in your folder)
from pdf_reader import extract_text_from_pdf
from nlp_matcher import match_resume_to_jd

app = Flask(__name__)
CORS(app)

DB_PATH = 'ats_database.db'

def init_db():
    """Initializes the database schema for persistence"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for all registered users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, email TEXT, mobile TEXT, password TEXT, role TEXT)''')
    # Table for candidate analysis results
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, score INTEGER, matched TEXT, 
        missing TEXT, explanation TEXT, timestamp DATETIME)''')
    # Table for activity tracking
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, action TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

def extract_email(text):
    """Regex logic to automate email retrieval from resume text"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else "candidate@example.com"

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
        email = extract_email(resume_text)
        analysis = match_resume_to_jd(resume_text, jd_text)
        
        # Save to candidates table
        cursor.execute('''INSERT INTO candidates (name, email, score, matched, missing, explanation, timestamp) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (filename, email, analysis['score'], analysis['matched_skills'], 
                        analysis['missing_skills'], analysis['explanation'], datetime.now()))
        
        # Create audit log entry
        cursor.execute('INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)',
                       (hr_email, f"Analyzed: {filename}", datetime.now()))

    conn.commit()
    conn.close()
    return jsonify({"message": "Successfully analyzed and saved to database"}), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM candidates ORDER BY timestamp DESC')
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data), 200

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
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)