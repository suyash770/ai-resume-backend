from flask import Flask, request, jsonify, session
from flask_cors import CORS
from nlp_engine import extract_skills, calculate_similarity
from pdf_reader import extract_text_from_pdf
from database import init_db, insert_many, get_candidates_by_user
from auth import create_users_table, register_user, verify_user
import uuid
import sqlite3

app = Flask(__name__)
CORS(app)

app.secret_key = "supersecretkey"

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
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        return jsonify(user)

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# ---------- AI Explanation ----------
def generate_explanation(score, matched, missing):
    if score > 80:
        level = "very strong"
    elif score >= 50:
        level = "moderate"
    else:
        level = "weak"

    return (
        f"This resume is a {level} match for the job description. "
        f"It matches key skills like {', '.join(matched) if matched else 'none'} "
        f"and lacks skills such as {', '.join(missing) if missing else 'none'}. "
        f"Overall similarity with the job description is {score}%."
    )


# ---------- PREDICT (NEW SESSION EACH TIME) ----------
@app.route("/predict", methods=["POST"])
def predict():
    jd_text = request.form.get("jd_text", "")

    if "jd_pdf" in request.files:
        jd_text = extract_text_from_pdf(request.files["jd_pdf"])

    pdf_files = request.files.getlist("resume_pdfs")

    session_id = str(uuid.uuid4())
    user_id = session.get("user_id")

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


# ---------- GET LATEST SESSION CANDIDATES ----------
@app.route("/candidates", methods=["GET"])
def candidates():
    user_id = session.get("user_id")

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


# ---------- LIST SESSIONS ----------
@app.route("/sessions", methods=["GET"])
def sessions():
    user_id = session.get("user_id")

    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT session_id
        FROM candidates
        WHERE user_id = ?
        ORDER BY rowid DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([r[0] for r in rows])


# ---------- GET SESSION DATA ----------
@app.route("/session/<sid>", methods=["GET"])
def session_data(sid):
    user_id = session.get("user_id")

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
