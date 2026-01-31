from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills
from pdf_reader import extract_text_from_pdf
from database import init_db, insert_many, get_all_candidates

app = Flask(__name__)
CORS(app)

# Initialize database once when server starts
init_db()


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


@app.route("/predict", methods=["POST"])
def predict():
    jd_text = request.form.get("jd_text", "")
    pdf_files = request.files.getlist("resume_pdfs")

    job_skills = extract_skills(jd_text)
    candidates_to_save = []

    # Process each uploaded resume
    for pdf_file in pdf_files:
        resume_text = extract_text_from_pdf(pdf_file)
        resume_skills = extract_skills(resume_text)

        matched = list(set(resume_skills) & set(job_skills))
        missing = list(set(job_skills) - set(matched))
        score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

        name = pdf_file.filename

        # Collect data (no DB write here)
        candidates_to_save.append(
            (name, score, ", ".join(matched), ", ".join(missing))
        )

    # Single fast DB write
    insert_many(candidates_to_save)

    return jsonify({"message": "All resumes processed"})


@app.route("/candidates", methods=["GET"])
def candidates():
    rows = get_all_candidates()
    result = []

    for row in rows:
        result.append({
            "name": row[0],
            "score": row[1],
            "matched": row[2],
            "missing": row[3]
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run()
