from flask import Blueprint, jsonify, session
from database.models import Resume, ExtractedData

jobs = Blueprint("jobs", __name__, url_prefix="/jobs")


# ============================================================
# JOB DATABASE
# ============================================================

JOB_DATABASE = [
    {
        "title": "Data Analyst",
        "company": "Analytics & Business Intelligence",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "sql", "pandas", "excel", "power bi",
            "tableau", "statistics", "data analysis", "data visualization"
        ],
        "search": "Data Analyst jobs"
    },
    {
        "title": "Data Scientist",
        "company": "AI & Data Science",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "machine learning", "pandas", "numpy",
            "scikit-learn", "statistics", "sql", "data analysis",
            "data visualization"
        ],
        "search": "Data Scientist jobs"
    },
    {
        "title": "Machine Learning Engineer",
        "company": "Machine Learning",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "machine learning", "deep learning",
            "tensorflow", "pytorch", "scikit-learn", "numpy", "pandas"
        ],
        "search": "Machine Learning Engineer jobs"
    },
    {
        "title": "AI Engineer",
        "company": "Artificial Intelligence",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "artificial intelligence", "machine learning",
            "deep learning", "llm", "rag", "nlp", "pytorch", "tensorflow"
        ],
        "search": "AI Engineer jobs"
    },
    {
        "title": "NLP Engineer",
        "company": "Natural Language Processing",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "nlp", "machine learning",
            "deep learning", "llm", "rag", "natural language processing"
        ],
        "search": "NLP Engineer jobs"
    },
    {
        "title": "Computer Vision Engineer",
        "company": "Computer Vision & AI",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "computer vision", "deep learning",
            "tensorflow", "pytorch", "opencv", "machine learning"
        ],
        "search": "Computer Vision Engineer jobs"
    },
    {
        "title": "Python Developer",
        "company": "Software Development",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "python", "flask", "fastapi", "sql",
            "git", "github", "api", "rest api"
        ],
        "search": "Python Developer jobs"
    },
    {
        "title": "AI / ML Intern",
        "company": "Artificial Intelligence",
        "location": "India / Remote",
        "experience": "Internship / Fresher",
        "skills": [
            "python", "machine learning", "artificial intelligence",
            "numpy", "pandas", "scikit-learn", "deep learning"
        ],
        "search": "AI ML Internship jobs"
    },
    {
        "title": "Business Intelligence Analyst",
        "company": "Business Intelligence",
        "location": "India / Remote",
        "experience": "0-2 Years",
        "skills": [
            "sql", "power bi", "tableau", "excel",
            "statistics", "data analysis", "data visualization"
        ],
        "search": "Business Intelligence Analyst jobs"
    }
]


# ============================================================
# NORMALIZATION
# ============================================================

SKILL_ALIASES = {
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "powerbi": "power bi",
    "power bi": "power bi",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "natural language processing": "nlp",
    "large language models": "llm",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "fast api": "fastapi",
    "restful api": "rest api",
    "restful apis": "rest api",
    "js": "javascript",
    "node js": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "mongo db": "mongodb",
    "c plus plus": "c++",
}


def normalize_skill(skill):
    if not skill:
        return ""

    value = str(skill).lower().strip()

    # Keep important symbols used in technical skills.
    value = value.replace("_", " ").replace("-", " ")

    # Collapse repeated whitespace.
    value = " ".join(value.split())

    return value


def canonical_skill(skill):
    value = normalize_skill(skill)

    # Because normalize_skill converts "-" to " ",
    # aliases are stored using the normalized form.
    aliases = {
        normalize_skill(key): value
        for key, value in SKILL_ALIASES.items()
    }

    return aliases.get(value, value)


# ============================================================
# RESUME SKILLS
# ============================================================

def parse_stored_skills(skills):
    """
    ExtractedData.skills is stored by resume.py as:
        ", ".join(information.get("skills", []))

    This function converts that stored string back into a
    normalized set.
    """
    if not skills:
        return set()

    if isinstance(skills, list):
        raw_skills = skills
    else:
        raw_skills = str(skills).split(",")

    result = set()

    for skill in raw_skills:
        canonical = canonical_skill(skill)
        if canonical:
            result.add(canonical)

    return result


def get_latest_resume(user_id):
    return (
        Resume.query
        .filter_by(user_id=user_id)
        .order_by(Resume.id.desc())
        .first()
    )


def get_resume_skills(resume):
    """
    Use the exact skills already extracted during upload.
    This avoids running the extractor a second time and makes
    recommendations consistent with the uploaded resume.
    """
    extracted = (
        ExtractedData.query
        .filter_by(resume_id=resume.id)
        .first()
    )

    if extracted and extracted.skills:
        return parse_stored_skills(extracted.skills)

    return set()


def get_resume_profile(resume):
    extracted = (
        ExtractedData.query
        .filter_by(resume_id=resume.id)
        .first()
    )

    if not extracted:
        return {}

    return {
        "name": extracted.name or "",
        "email": extracted.email or "",
        "phone": extracted.phone or "",
    }


# ============================================================
# ROLE INFERENCE
# ============================================================

ROLE_KEYWORDS = {
    "Data Scientist": [
        "data science", "machine learning", "statistics",
        "pandas", "scikit-learn", "numpy"
    ],
    "Data Analyst": [
        "data analysis", "power bi", "tableau",
        "excel", "sql", "statistics"
    ],
    "Machine Learning Engineer": [
        "machine learning", "deep learning",
        "tensorflow", "pytorch", "scikit-learn"
    ],
    "AI Engineer": [
        "artificial intelligence", "machine learning",
        "deep learning", "llm", "rag", "nlp"
    ],
    "NLP Engineer": [
        "nlp", "llm", "rag"
    ],
    "Computer Vision Engineer": [
        "computer vision", "opencv", "tensorflow",
        "pytorch", "deep learning"
    ],
    "Python Developer": [
        "python", "flask", "fastapi", "api", "rest api", "sql"
    ],
    "AI / ML Intern": [
        "artificial intelligence", "machine learning",
        "python", "deep learning"
    ],
    "Business Intelligence Analyst": [
        "power bi", "tableau", "sql", "excel",
        "data visualization"
    ],
}


def infer_roles(resume_skills):
    role_scores = []

    for role, keywords in ROLE_KEYWORDS.items():
        matched = 0

        for keyword in keywords:
            if canonical_skill(keyword) in resume_skills:
                matched += 1

        if matched:
            role_scores.append({
                "role": role,
                "score": matched,
                "matched_keywords": matched,
            })

    role_scores.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return role_scores


# ============================================================
# JOB MATCHING
# ============================================================

def calculate_job_match(resume_skills, job_skills):
    job_set = {
        canonical_skill(skill)
        for skill in job_skills
        if canonical_skill(skill)
    }

    if not job_set:
        return {
            "score": 0.0,
            "matched": [],
            "missing": []
        }

    matched = sorted(resume_skills.intersection(job_set))
    missing = sorted(job_set - resume_skills)

    score = round(
        (len(matched) / len(job_set)) * 100,
        1
    )

    return {
        "score": score,
        "matched": matched,
        "missing": missing
    }


# ============================================================
# JOB URLS
# ============================================================

def build_job_urls(search):
    from urllib.parse import quote

    query = quote(search)

    return {
        "linkedin": (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={query}"
        ),
        "indeed": (
            "https://in.indeed.com/jobs?"
            f"q={query}"
        ),
        "naukri": (
            "https://www.naukri.com/"
            f"{query.lower().replace(' ', '-')}-jobs"
        )
    }


# ============================================================
# RECOMMENDED JOBS
# ============================================================

@jobs.get("/recommended")
def recommended_jobs():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify(
            success=False,
            message="Please login first."
        ), 401

    resume = get_latest_resume(user_id)

    if not resume:
        return jsonify(
            success=False,
            message="Please upload a resume first."
        ), 404

    try:
        # IMPORTANT:
        # Read the skills saved during the current user's
        # latest resume upload.
        resume_skills = get_resume_skills(resume)

        if not resume_skills:
            return jsonify({
                "success": True,
                "jobs": [],
                "resume_skills": [],
                "recommended_roles": [],
                "profile": get_resume_profile(resume),
                "message": (
                    "No technical skills were extracted from "
                    "the latest resume."
                )
            })

        inferred_roles = infer_roles(resume_skills)
        top_roles = inferred_roles[:3]

        results = []

        for job in JOB_DATABASE:
            match = calculate_job_match(
                resume_skills,
                job["skills"]
            )

            # ----------------------------------------------------
            # DO NOT SHOW ZERO-MATCH JOBS.
            # This was one of the main reasons the same jobs
            # appeared for every resume.
            # ----------------------------------------------------
            if not match["matched"]:
                continue

            # Small role bonus only when the inferred role
            # exactly corresponds to this job title.
            role_bonus = 0

            for role in top_roles:
                if role["role"].lower() == job["title"].lower():
                    role_bonus = min(
                        role["score"] * 2,
                        10
                    )
                    break

            final_score = min(
                round(match["score"] + role_bonus, 1),
                100
            )

            urls = build_job_urls(job["search"])

            results.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "experience": job["experience"],
                "skills": job["skills"],
                "matched_skills": match["matched"],
                "missing_skills": match["missing"],
                "match_score": final_score,
                "skill_match_score": match["score"],
                "role_match": role_bonus > 0,
                "urls": urls,
                "url": urls["linkedin"]
            })

        # Highest skill match first.
        results.sort(
            key=lambda item: (
                item["match_score"],
                len(item["matched_skills"]),
                -len(item["missing_skills"])
            ),
            reverse=True
        )

        # Return at most 6 useful recommendations.
        results = results[:6]

        profile = get_resume_profile(resume)

        return jsonify({
            "success": True,
            "jobs": results,
            "resume_id": resume.id,
            "resume_skills": sorted(resume_skills),
            "recommended_roles": top_roles,
            "profile": {
                **profile,
                "skills_count": len(resume_skills),
                "top_role": (
                    top_roles[0]["role"]
                    if top_roles
                    else "General"
                )
            }
        })

    except Exception as error:
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to generate job recommendations.",
            "error": str(error)
        }), 500
