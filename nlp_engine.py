from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS_DB = [
    "python", "java", "c++", "machine learning", "data science",
    "sql", "html", "css", "javascript", "flask", "react",
    "git", "docker", "aws"
]

def extract_skills(text):
    text = text.lower()
    found = []
    for skill in SKILLS_DB:
        if skill in text:
            found.append(skill)
    return list(set(found))


def calculate_similarity(resume_text, jd_text):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(score * 100)
