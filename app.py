from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills
from pdf_reader import extract_text_from_pdf
from database import init_db, insert_many, get_all_candidates, clear_candidates

app = Flask(__name__)
CORS(app)

init_db()


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


@app.route("/predict", methods=["POST"])
def predict():
    jd_text = request.form.get("jd_text", "")
    pdf_files = request.files.getlist("resume_pdfs")

    # 🔥 CLEAR OLD DATA BEFORE NEW ANALYSIS
    clear_candidates()

    job_skills = extract_skills(jd_text)
    candidates_to_save = []

    for pdf_file in pdf_files:
        resume_text = extract_text_from_pdf(pdf_file)
        resume_skills = extract_skills(resume_text)

        matched = list(set(resume_skills) & set(job_skills))
        missing = list(set(job_skills) - set(matched))
        score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

        candidates_to_save.append(
            (pdf_file.filename, score, ", ".join(matched), ", ".join(missing))
        )

    insert_many(candidates_to_save)

    return jsonify({"status": "done"})


@app.route("/candidates", methods=["GET"])
def candidates():
    rows = get_all_candidates()
    return jsonify([
        {"name": r[0], "score": r[1], "matched": r[2], "missing": r[3]}
        for r in rows
    ])


if __name__ == "__main__":
    app.run()
