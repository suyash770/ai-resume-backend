SKILLS_DB = [
    "python", "java", "c++", "machine learning", "data science",
    "sql", "html", "css", "javascript", "flask", "react",
    "git", "docker", "aws"
]

def extract_skills(text):
    text = text.lower()
    skills = []

    for skill in SKILLS_DB:
        if skill in text:
            skills.append(skill)

    # Bonus scoring for frequency
    skills = list(set(skills))
    return skills
