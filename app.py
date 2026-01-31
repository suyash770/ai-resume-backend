from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills
from pdf_reader import extract_text_from_pdf

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


@app.route("/predict", methods=["POST"])
def predict():
    jd_text = request.form.get("jd_text", "")

    # Get resume text from PDF
    if "resume_pdf" in request.files:
        pdf_file = request.files["resume_pdf"]
        resume_text = extract_text_from_pdf(pdf_file)
    else:
        resume_text = ""

    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(jd_text)

    matched = list(set(resume_skills) & set(job_skills))
    missing = list(set(job_skills) - set(matched))

    score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

    return jsonify({
        "score": score,
        "resume_skills": resume_skills,
        "matched_skills": matched,
        "missing_skills": missing
    })


if __name__ == "__main__":
    app.run()
