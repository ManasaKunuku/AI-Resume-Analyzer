import os
import re
from collections import Counter

import docx
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "html", "css",
    "react", "angular", "vue", "node.js", "flask", "django", "fastapi", "spring boot",
    "rest api", "graphql", "machine learning", "deep learning", "nlp", "data analysis",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "power bi", "tableau",
    "excel", "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "linux",
    "mysql", "postgresql", "mongodb", "redis", "firebase", "communication", "leadership",
    "problem solving", "agile", "scrum", "testing", "selenium", "figma"
]

SECTION_PATTERNS = {
    "Contact details": r"\b(email|phone|mobile|linkedin|github)\b",
    "Professional summary": r"\b(summary|objective|profile)\b",
    "Education": r"\b(education|bachelor|master|university|college|degree)\b",
    "Experience": r"\b(experience|employment|work history|internship)\b",
    "Projects": r"\b(projects|personal projects|academic projects)\b",
    "Skills": r"\b(skills|technical skills|technologies)\b",
}


def extract_text(path):
    extension = os.path.splitext(path)[1].lower()
    if extension == ".pdf":
        chunks = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    if extension == ".docx":
        document = docx.Document(path)
        return "\n".join(p.text for p in document.paragraphs)
    if extension == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    raise ValueError("Unsupported file format.")


def find_skills(text):
    normalized = re.sub(r"\s+", " ", text.lower())
    found = []
    for skill in SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, normalized):
            found.append(skill)
    return sorted(found)


def analyze_resume(resume_text, job_description):
    resume_skills = set(find_skills(resume_text))
    job_skills = set(find_skills(job_description))
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        similarity = 0.0

    if job_skills:
        skill_score = len(matched) / len(job_skills)
        score = round((0.65 * skill_score + 0.35 * similarity) * 100)
    else:
        score = round(similarity * 100)

    lower_resume = resume_text.lower()
    sections_found = [name for name, pattern in SECTION_PATTERNS.items()
                      if re.search(pattern, lower_resume)]
    sections_missing = [name for name in SECTION_PATTERNS if name not in sections_found]

    suggestions = []
    if missing:
        suggestions.append("If you genuinely have them, add evidence for these job-related skills: " + ", ".join(missing[:12]) + ".")
    if "Projects" in sections_missing:
        suggestions.append("Add a Projects section with 2–3 relevant projects, technologies used, and measurable outcomes.")
    if "Experience" in sections_missing:
        suggestions.append("Include internships, volunteering, freelance work, or practical experience where relevant.")
    if "Professional summary" in sections_missing:
        suggestions.append("Add a short 2–3 line summary tailored to the target role.")
    if "Education" in sections_missing:
        suggestions.append("Make your education, qualification, institution, and graduation year easy to find.")
    if "Skills" in sections_missing:
        suggestions.append("Add a clearly labeled Skills section containing only skills you can confidently discuss.")
    if len(resume_text.split()) < 150:
        suggestions.append("Your resume text looks brief. Add relevant details while keeping the resume concise.")
    if not suggestions:
        suggestions.append("Good structure detected. Strengthen bullets with specific actions, tools, and measurable results.")

    return {
        "score": max(0, min(100, score)),
        "similarity": round(similarity * 100, 1),
        "resume_skills": sorted(resume_skills),
        "job_skills": sorted(job_skills),
        "matched_skills": matched,
        "missing_skills": missing,
        "sections_found": sections_found,
        "sections_missing": sections_missing,
        "suggestions": suggestions,
    }
