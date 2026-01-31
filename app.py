from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills, calculate_similarity
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

    if "jd_pdf" in request.files:
        jd_text = extract_text_from_pdf(request.files["jd_pdf"])

    pdf_files = request.files.getlist("resume_pdfs")

    clear_candidates()
    candidates_to_save = []

    for pdf_file in pdf_files:
        resume_text = extract_text_from_pdf(pdf_file)

        # 🔥 REAL AI SCORE
        score = calculate_similarity(resume_text, jd_text)

        resume_skills = extract_skills(resume_text)
        job_skills = extract_skills(jd_text)

        matched = list(set(resume_skills) & set(job_skills))
        missing = list(set(job_skills) - set(matched))

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
