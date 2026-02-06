import os
import re
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Helper modules (Ensure these files are in your project directory)
from pdf_reader import extract_text_from_pdf
from nlp_matcher import match_resume_to_jd

app = Flask(__name__)
CORS(app)

DB_PATH = 'ats_database.db'

def init_db():
    """Initializes the database and creates persistent tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users Table: Stores registered credentials
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, 
        email TEXT UNIQUE, 
        mobile TEXT, 
        password TEXT, 
        role TEXT)''')
    
    # Candidates Table: Stores ATS analysis history
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, 
        email TEXT, 
        score INTEGER, 
        matched TEXT, 
        missing TEXT, 
        explanation TEXT, 
        timestamp DATETIME)''')
    
    # Logs Table: For system audit trails
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, 
        action TEXT, 
        timestamp DATETIME)''')
    
    conn.commit()
    conn.close()

init_db()

# --- UTILITY FUNCTIONS ---

def extract_email(text):
    """Automated email extraction using Regex"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else "candidate@example.com"

# --- AUTHENTICATION & RECOVERY ---

@app.route('/register', methods=['POST'])
def register():
    """Saves new user data to the SQL database"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO users (username, email, mobile, password, role) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (data['name'], data['email'], data['mobile'], data['pass'], data['role']))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "This email is already registered!"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Verifies credentials against database records"""
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
        # Determine target dashboard based on verified role
        redirect_page = "admin.html" if user_data['role'] == 'admin' else \
                        "index.html" if user_data['role'] == 'hr' else "candidate.html"
        return jsonify({"user": user_data, "redirect": redirect_page}), 200
    return jsonify({"error": "Invalid email, password, or role!"}), 401

@app.route('/reset_password', methods=['POST'])
def reset_password():
    """Verified password update logic"""
    data = request.json
    email = data.get('email')
    mobile = data.get('mobile')
    new_pass = data.get('new_pass')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email=? AND mobile=?', (email, mobile))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET password=? WHERE id=?', (new_pass, user[0]))
        cursor.execute('INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)',
                       (email, "Password Reset Performed", datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({"message": "Password updated successfully! ✅"}), 200
    
    conn.close()
    return jsonify({"error": "Verification failed. Identity mismatch."}), 401

# --- ANALYSIS & LOGGING ---



@app.route('/predict', methods=['POST'])
def predict():
    """Processes analysis and logs the HR operator's action"""
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
        
        cursor.execute('''INSERT INTO candidates (name, email, score, matched, missing, explanation, timestamp) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (filename, email, analysis['score'], analysis['matched_skills'], 
                        analysis['missing_skills'], analysis['explanation'], datetime.now()))
        
        cursor.execute('INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)',
                       (hr_email, f"Analyzed Resume: {filename}", datetime.now()))

    conn.commit()
    conn.close()
    return jsonify({"message": "Batch analysis successful"}), 200

# --- ADMINISTRATIVE CONTROL ---

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    """Retrieves full user list for Admin management"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, mobile FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users), 200

@app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Permanently removes user and logs the deletion"""
    admin_email = request.args.get('admin_email')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    cursor.execute('INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)',
                   (admin_email, f"Deleted User ID: {user_id}", datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({"message": "User deleted"}), 200

@app.route('/admin/logs', methods=['GET'])
def get_logs():
    """Retrieves system logs"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs), 200

@app.route('/admin/stats', methods=['GET'])
def get_stats():
    """Calculates global metrics for Admin view"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM candidates')
    total_runs = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    conn.close()
    return jsonify({"total_runs": total_runs, "total_users": total_users}), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    """Fetches candidate data for HR view"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM candidates ORDER BY timestamp DESC')
    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(candidates), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)