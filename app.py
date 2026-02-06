import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import your PDF reader and NLP/Matching scripts
# Ensure these files are in the same directory as app.py
from pdf_reader import extract_text_from_pdf
from nlp_matcher import match_resume_to_jd

app = Flask(__name__)
CORS(app) # Enables frontend-backend communication

# Temporary storage for candidate analysis results
# In a real app, this would be a database (SQLite/PostgreSQL)
candidates_db = []

def extract_email(text):
    """
    Uses Regex to find the first email address in the resume text.
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else "candidate@example.com"

@app.route('/predict', methods=['POST'])
def predict():
    global candidates_db
    
    # Check if files were uploaded
    if 'resume_pdfs' not in request.files:
        return jsonify({"error": "No resumes uploaded"}), 400

    # Get Job Description (from text box or PDF)
    jd_text = request.form.get('jd_text', '')
    if 'jd_pdf' in request.files:
        jd_file = request.files['jd_pdf']
        jd_text = extract_text_from_pdf(jd_file)

    if not jd_text:
        return jsonify({"error": "Job description is missing"}), 400

    resumes = request.files.getlist('resume_pdfs')
    analysis_results = []

    for resume_file in resumes:
        filename = secure_filename(resume_file.filename)
        
        # 1. Extract text from PDF
        resume_text = extract_text_from_pdf(resume_file)
        
        # 2. Extract Candidate Email automatically
        email = extract_email(resume_text)
        
        # 3. Perform Match Analysis
        # This function should return: score, matched_skills, missing_skills, explanation
        analysis = match_resume_to_jd(resume_text, jd_text)
        
        candidate_entry = {
            "name": filename,
            "email": email,
            "score": analysis['score'],
            "matched": analysis['matched_skills'],
            "missing": analysis['missing_skills'],
            "explanation": analysis['explanation']
        }
        
        analysis_results.append(candidate_entry)
        candidates_db.append(candidate_entry)

    return jsonify({
        "message": f"Analyzed {len(analysis_results)} resumes successfully",
        "results": analysis_results
    }), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    """
    Returns the list of analyzed candidates for the dashboard table.
    """
    return jsonify(candidates_db), 200

@app.route('/clear', methods=['POST'])
def clear_data():
    """
    Clears the temporary candidate database.
    """
    global candidates_db
    candidates_db = []
    return jsonify({"message": "Data cleared"}), 200

if __name__ == '__main__':
    # Get port from environment (required for Render/Heroku)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)