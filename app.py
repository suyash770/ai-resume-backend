from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills, calculate_similarity
from pdf_reader import extract_text_from_pdf
from database import init_db, insert_many
from auth import create_users_table, register_user, verify_user
import uuid
import sqlite3

app = Flask(__name__)
CORS(app)

init_db()
create_users_table()


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


# ---------- AUTH ----------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    register_user(data["email"], data["password"], data["role"])
    return jsonify({"message": "User registered"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = verify_user(data["email"], data["password"])
    if user:
        return jsonify(user)
    return jsonify({"error": "Invalid credentials"}), 401


# ---------- AI Explanation ----------
def generate_explanation(score, matched, missing):
    if score > 80:
        level = "very strong"
    elif score >= 50:
        level = "moderate"
    else:
        level = "weak"

    return (
        f"This resume is a {level} match. "
        f"Matched skills: {', '.join(matched)}. "
        f"Missing skills: {', '.join(missing)}. "
        f"Overall score: {score}%."
    )


# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    jd_text = request.form.get("jd_text", "")
    user_id = request.form.get("user_id")

    if "jd_pdf" in request.files:
        jd_text = extract_text_from_pdf(request.files["jd_pdf"])

    pdf_files = request.files.getlist("resume_pdfs")
    session_id = str(uuid.uuid4())

    candidates_to_save = []

    for pdf_file in pdf_files:
        resume_text = extract_text_from_pdf(pdf_file)
        score = calculate_similarity(resume_text, jd_text)

        resume_skills = extract_skills(resume_text)
        job_skills = extract_skills(jd_text)

        matched = list(set(resume_skills) & set(job_skills))
        missing = list(set(job_skills) - set(matched))
        explanation = generate_explanation(score, matched, missing)

        candidates_to_save.append(
            (
                user_id,
                session_id,
                pdf_file.filename,
                score,
                ", ".join(matched),
                ", ".join(missing),
                explanation
            )
        )

    insert_many(candidates_to_save)
    return jsonify({"status": "done"})


# ---------- GET CANDIDATES ----------
@app.route("/candidates/<user_id>")
def candidates(user_id):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM candidates
        WHERE user_id = ?
        ORDER BY rowid DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "name": r[2],
            "score": r[3],
            "matched": r[4],
            "missing": r[5],
            "explanation": r[6]
        }
        for r in rows
    ])


# ---------- SESSIONS ----------
@app.route("/sessions/<user_id>")
def sessions(user_id):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT session_id
        FROM candidates
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([r[0] for r in rows])


@app.route("/session/<user_id>/<sid>")
def session_data(user_id, sid):
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM candidates
        WHERE user_id = ? AND session_id = ?
    """, (user_id, sid))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "name": r[2],
            "score": r[3],
            "matched": r[4],
            "missing": r[5],
            "explanation": r[6]
        }
        for r in rows
    ])


if __name__ == "__main__":
    app.run()
