from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running"

# Job description skills (AI compares resume with this)
JOB_DESCRIPTION = """
python machine learning data science sql javascript flask docker aws
"""

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    resume_text = data.get("resume_text", "")

    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(JOB_DESCRIPTION)

    matched = list(set(resume_skills) & set(job_skills))
    missing = list(set(job_skills) - set(matched))

    # Prevent division by zero
    if len(job_skills) == 0:
        score = 0
    else:
        score = int((len(matched) / len(job_skills)) * 100)

    return jsonify({
        "score": score,
        "resume_skills": resume_skills,
        "matched_skills": matched,
        "missing_skills": missing
    })

if __name__ == "__main__":
    app.run()
