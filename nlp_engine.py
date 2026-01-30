SKILLS_DB = [
    "python", "java", "c++", "machine learning", "data science",
    "sql", "html", "css", "javascript", "flask", "django",
    "react", "git", "docker", "aws"
]

def extract_skills(text):
    text = text.lower()
    found = []
    for skill in SKILLS_DB:
        if skill in text:
            found.append(skill)
    return list(set(found))
