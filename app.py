from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


@app.route("/predict", methods=["POST"])
def predict():
    # Get data from frontend
    data = request.get_json(force=True)

    resume_text = data.get("resume_text", "")
    jd_text = data.get("jd_text", "")

    # Extract skills from resume and JD
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(jd_text)

    # Find matched and missing skills
    matched = list(set(resume_skills) & set(job_skills))
    missing = list(set(job_skills) - set(matched))

    # Calculate ATS score safely
    score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

    # Send result back to frontend
    return jsonify({
        "score": score,
        "resume_skills": resume_skills,
        "matched_skills": matched,
        "missing_skills": missing
    })


if __name__ == "__main__":
    app.run()
