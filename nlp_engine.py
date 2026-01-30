import spacy

nlp = spacy.load("en_core_web_sm")

# Skill database
SKILLS_DB = [
    "python", "java", "c++", "machine learning", "data science", "sql",
    "html", "css", "javascript", "flask", "django", "react", "node",
    "mongodb", "git", "docker", "aws", "deep learning"
]

def extract_skills(text):
    text = text.lower()
    doc = nlp(text)

    found_skills = set()

    for token in doc:
        if token.text in SKILLS_DB:
            found_skills.add(token.text)

    # Check multi-word skills manually
    for skill in SKILLS_DB:
        if skill in text:
            found_skills.add(skill)

    return list(found_skills)
