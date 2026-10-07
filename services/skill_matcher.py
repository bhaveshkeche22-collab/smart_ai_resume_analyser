import re
from services.resume_extractor import SKILL_LIST

ALIASES = {
    "sklearn": "scikit-learn",
    "nodejs": "node.js",
    "large language model": "large language models",
    "natural language processing": "nlp",
    "powerbi": "power bi",
    "ml": "machine learning",
    "ai": "artificial intelligence",
}


def normalize_skill(skill):
    value = re.sub(r"\s+", " ", str(skill or "").strip().lower())
    return ALIASES.get(value, value)


def extract_required_skills(text):
    text = str(text or "").lower()
    found = set()
    for skill in sorted(SKILL_LIST, key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)", text):
            found.add(normalize_skill(skill))
    return sorted(found)


def match_skills(resume_skills, job_description):
    resume = {normalize_skill(s) for s in (resume_skills or [])}
    required = set(extract_required_skills(job_description))
    matched = sorted(resume & required)
    missing = sorted(required - resume)
    score = round((len(matched) / len(required)) * 100, 2) if required else 0.0
    return {
        "required_skills": sorted(required),
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": score,
        "matched_count": len(matched),
        "required_count": len(required),
    }
