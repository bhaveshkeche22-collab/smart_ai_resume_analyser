import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from services.skill_matcher import match_skills


STOPWORDS = {
    "and", "the", "with", "for", "from", "that", "this", "are", "will",
    "you", "your", "our", "have", "has", "into", "using", "use", "work",
    "role", "job", "who", "about", "their", "they", "them", "can",
    "should", "must", "able", "years", "year", "team", "good", "strong",
    "looking", "responsible", "responsibilities", "candidate", "skills",
    "experience", "required", "requirements", "developer", "development",
}


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def tfidf_similarity(resume_text, job_description):
    resume_text = _clean_text(resume_text)
    job_description = _clean_text(job_description)

    if not resume_text or not job_description:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=6000
        )

        matrix = vectorizer.fit_transform(
            [resume_text, job_description]
        )

        score = float(
            cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        ) * 100

        return round(max(0.0, min(100.0, score)), 2)

    except ValueError:
        return 0.0


def keyword_coverage(resume_text, job_description):
    resume_text = _clean_text(resume_text)
    job_description = _clean_text(job_description)

    resume_words = set(
        re.findall(
            r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}",
            resume_text
        )
    )

    job_words = set(
        re.findall(
            r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}",
            job_description
        )
    )

    important = {
        word for word in job_words
        if word not in STOPWORDS
    }

    if not important:
        return 0.0, []

    matched = sorted(
        resume_words.intersection(important)
    )

    return round(
        len(matched) / len(important) * 100,
        2
    ), matched


def _section_score(
    value,
    resume_text,
    job_description,
    terms
):
    section = _clean_text(value)
    full_resume = _clean_text(resume_text)
    job = _clean_text(job_description)

    relevant = [
        term.lower()
        for term in terms
        if term.lower() in job
    ]

    # If the job description does not mention
    # this category, do not penalize the resume.
    if not relevant:
        return 100.0

    # Use the extracted section AND the complete resume.
    evidence = f"{section} {full_resume}".strip()

    matched = sum(
        1
        for term in relevant
        if term in evidence
    )

    return round(
        matched / len(relevant) * 100,
        2
    )


def calculate_ats(
    resume_information,
    resume_text,
    job_description
):
    """
    Project ATS Score.

    Skills Match  = 40 points
    Education     = 15 points
    Projects      = 15 points
    Experience    = 15 points
    Keywords      = 15 points

    Total = 100.
    """

    resume_information = resume_information or {}

    resume_text = str(
        resume_text or ""
    )

    job_description = str(
        job_description or ""
    )

    # ---------------------------------------------------------
    # SKILLS
    # ---------------------------------------------------------

    skill = match_skills(
        resume_information.get("skills", []) or [],
        job_description
    ) or {}

    skill_score = float(
        skill.get("match_score", 0) or 0
    )

    # ---------------------------------------------------------
    # TF-IDF SIMILARITY
    # ---------------------------------------------------------

    similarity = tfidf_similarity(
        resume_text,
        job_description
    )

    # ---------------------------------------------------------
    # KEYWORDS
    # ---------------------------------------------------------

    keywords, matched_keywords = keyword_coverage(
        resume_text,
        job_description
    )

    # ---------------------------------------------------------
    # EDUCATION
    # ---------------------------------------------------------

    education = _section_score(
        resume_information.get("education", ""),
        resume_text,
        job_description,
        [
            "b.tech",
            "btech",
            "b.e",
            "bachelor",
            "master",
            "m.tech",
            "mca",
            "mba",
            "degree",
            "computer science",
            "engineering",
            "science",
            "statistics"
        ]
    )

    # ---------------------------------------------------------
    # PROJECTS
    # ---------------------------------------------------------

    projects = _section_score(
        resume_information.get("projects", ""),
        resume_text,
        job_description,
        [
            "project",
            "python",
            "sql",
            "machine learning",
            "data analysis",
            "deep learning",
            "api",
            "flask",
            "fastapi",
            "react",
            "tensorflow",
            "pandas",
            "numpy",
            "backend",
            "database"
        ]
    )

    # ---------------------------------------------------------
    # EXPERIENCE
    # ---------------------------------------------------------

    experience = _section_score(
        resume_information.get("experience", ""),
        resume_text,
        job_description,
        [
            "internship",
            "employment",
            "experience",
            "software",
            "engineering",
            "machine learning",
            "analytics",
            "development",
            "python",
            "sql",
            "backend",
            "api",
            "database"
        ]
    )

    # ---------------------------------------------------------
    # FINAL ATS SCORE
    # ---------------------------------------------------------

    ats = (
        skill_score * 0.40
        + education * 0.15
        + projects * 0.15
        + experience * 0.15
        + keywords * 0.15
    )

    ats = round(
        max(0.0, min(100.0, ats)),
        2
    )

    return {
        "ats_score": ats,

        "skill_match_score": round(
            skill_score, 2
        ),

        "similarity_score": similarity,

        "education_score": round(
            education, 2
        ),

        "project_score": round(
            projects, 2
        ),

        "experience_score": round(
            experience, 2
        ),

        "keyword_score": round(
            keywords, 2
        ),

        "required_skills": skill.get(
            "required_skills", []
        ),

        "matched_skills": skill.get(
            "matched_skills", []
        ),

        "missing_skills": skill.get(
            "missing_skills", []
        ),

        "matched_keywords": matched_keywords[:100],

        "matched_count": skill.get(
            "matched_count", 0
        ),

        "required_count": skill.get(
            "required_count", 0
        )
    }


def build_recommendation(
    analysis,
    information
):
    suggestions = []

    missing = analysis.get(
        "missing_skills", []
    ) or []

    if missing:
        suggestions.append(
            "Add truthful evidence for: "
            + ", ".join(missing[:8])
            + "."
        )

    if analysis.get(
        "keyword_score", 0
    ) < 60:
        suggestions.append(
            "Use important job-description keywords naturally "
            "in your skills, projects, and experience sections."
        )

    if analysis.get(
        "similarity_score", 0
    ) < 50:
        suggestions.append(
            "Rewrite the summary and strongest project bullets "
            "to align with the target role."
        )

    if not information.get("education"):
        suggestions.append(
            "Add a clearly labeled Education section with degree, "
            "institution, dates, and CGPA/percentage."
        )

    if not information.get("projects"):
        suggestions.append(
            "Add relevant projects with technologies and measurable outcomes."
        )

    if not information.get("experience"):
        suggestions.append(
            "Add internship, work, or practical experience where applicable."
        )

    if not suggestions:
        suggestions.append(
            "Keep the formatting consistent and quantify achievements where possible."
        )

    score = float(
        analysis.get("ats_score", 0) or 0
    )

    if score >= 80:
        summary = (
            "Strong alignment with the selected job description."
        )

    elif score >= 60:
        summary = (
            "Moderate alignment. Targeted changes can improve the match."
        )

    else:
        summary = (
            "Several gaps remain between the resume "
            "and the selected job description."
        )

    return {
        "summary": summary,
        "suggestions": suggestions,
        "provider": "local"
    }