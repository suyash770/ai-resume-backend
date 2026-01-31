import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_engine import extract_skills
from pdf_reader import extract_text_from_pdf
from database import insert_many, get_all_candidates

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "AI Resume ATS Backend Running"


@app.route("/predict", methods=["POST"])
def predict():
    start_total = time.time()

    jd_text = request.form.get("jd_text", "")
    pdf_files = request.files.getlist("resume_pdfs")

    job_skills = extract_skills(jd_text)
    candidates_to_save = []

    for pdf_file in pdf_files:
        print("---- Processing:", pdf_file.filename)

        # -------- PDF READ TIMER --------
        t1 = time.time()
        resume_text = extract_text_from_pdf(pdf_file)
        t2 = time.time()
        print("PDF read time:", round(t2 - t1, 2), "seconds")

        # -------- SKILL EXTRACT TIMER --------
        resume_skills = extract_skills(resume_text)
        t3 = time.time()
        print("Skill extract time:", round(t3 - t2, 2), "seconds")

        matched = list(set(resume_skills) & set(job_skills))
        missing = list(set(job_skills) - set(matched))
        score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

        candidates_to_save.append(
            (pdf_file.filename, score, ", ".join(matched), ", ".join(missing))
        )

    # -------- SINGLE FAST DB WRITE --------
    insert_many(candidates_to_save)

    print("Total request time:", round(time.time() - start_total, 2), "seconds")

    return jsonify({"status": "done"})


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
