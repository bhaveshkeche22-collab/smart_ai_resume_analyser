import re
from typing import Dict, List, Optional


# ============================================================
# AI RESUME ANALYZER - CORRECTED GENERIC RESUME EXTRACTOR
# ============================================================
# Public API:
#     extract_resume_information(text)
#
# Designed for text extracted from PDF resumes (for example,
# pdfplumber output).
#
# Improvements:
# - Robust email extraction, including PDF line/column splits.
# - Avoids treating skills as email usernames.
# - Generic name extraction.
# - Generic phone extraction.
# - Education extraction keeps complete education records.
# - Skills are returned as individual values.
# - Experience and projects are section-aware and NOT hard-coded
#   to one particular resume.
# - Handles common resume section headings and wrapped lines.
# ============================================================


SKILL_LIST = [
    "python", "java", "c", "c++", "c#", "javascript", "typescript",
    "html", "css", "react", "angular", "vue",
    "node.js", "nodejs", "flask", "fastapi", "django",
    "mysql", "postgresql", "postgres", "mongodb", "sql", "firebase",
    "pandas", "numpy", "scikit-learn", "sklearn",
    "matplotlib", "seaborn", "power bi", "tableau",
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras",
    "rag", "generative ai", "llm",
    "large language model", "large language models",
    "aws", "azure", "google cloud", "docker",
    "git", "github", "linux",
    "rest api", "api", "data structures", "algorithms", "dsa",
    "scipy", "opencv", "streamlit", "langchain", "chromadb",
    "powerpoint", "excel", "word",
    "data analysis", "data visualization", "statistics", "etl", "r"
]

SKILL_SET = {s.lower() for s in SKILL_LIST}

SECTION_ALIASES = {
    "education": {
        "education", "educational background", "academic details",
        "academic background", "qualification", "qualifications",
        "academic qualification"
    },
    "experience": {
        "experience", "professional experience", "work experience",
        "employment", "employment history", "internship", "internships",
        "work history", "industrial experience"
    },
    "projects": {
        "projects", "project", "personal projects",
        "academic projects", "major projects", "key projects"
    },
    "skills": {
        "skills", "technical skills", "key skills", "technical expertise",
        "technologies", "technology stack", "core competencies"
    },
    "certifications": {
        "certifications", "certificates", "courses", "training"
    },
    "achievements": {
        "achievements", "awards", "honors"
    },
    "summary": {
        "profile", "professional summary", "summary", "objective",
        "career objective", "about me"
    },
    "contact": {
        "contact", "contact details", "personal details"
    },
    "languages": {"languages", "language"},
    "interests": {"interests", "hobbies", "hobby"},
}

ALL_SECTION_HEADERS = {
    alias
    for aliases in SECTION_ALIASES.values()
    for alias in aliases
}

DEGREE_PATTERNS = [
    r"\bph\.?\s*d\.?\b",
    r"\bdoctor(?:ate)?\b",
    r"\bm\.?\s*tech\b",
    r"\bm\.?\s*e\.?\b(?!\w)",
    r"\bmca\b",
    r"\bmba\b",
    r"\bm\.?\s*sc\b",
    r"\bm\.?\s*com\b",
    r"\bmaster(?:'s)?\s+of\b",
    r"\bb\.?\s*tech\b",
    r"\bb\.?\s*e\.?\b(?!\w)",
    r"\bbca\b",
    r"\bb\.?\s*sc\b",
    r"\bb\.?\s*com\b",
    r"\bbachelor(?:'s)?\s+of\b",
    r"\bdiploma\b",
    r"\bhsc\b",
    r"\b12(?:th)?(?:\s+grade)?\b",
    r"\bssc\b",
    r"\b10(?:th)?(?:\s+grade)?\b",
]

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:0?[1-9]|1[0-2])[/.-]\d{2,4}"
    r"|(?:19|20)\d{2}\s*[-–—]\s*(?:19|20)\d{2}"
    r"|(?:19|20)\d{2}"
    r"|present|current"
    r")\b",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])"
    r"[A-Za-z0-9._%+-]+"
    r"\s*@\s*"
    r"[A-Za-z0-9.-]+"
    r"\s*\.\s*[A-Za-z]{2,}"
    r"(?![\w.-])",
    re.IGNORECASE,
)

PHONE_PATTERNS = [
    re.compile(r"(?<!\d)\+91[\s.-]?[6-9]\d{4}[\s.-]?\d{5}(?!\d)"),
    re.compile(r"(?<!\d)91[\s.-]?[6-9]\d{4}[\s.-]?\d{5}(?!\d)"),
    re.compile(r"(?<!\d)[6-9]\d{4}[\s.-]?\d{5}(?!\d)"),
    re.compile(r"(?<!\d)\+\d{1,3}[\s.-]?\d{7,12}(?!\d)"),
]


# ============================================================
# BASIC NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = str(text)

    replacements = {
        "\xa0": " ",
        "\u2022": " ",
        "\u25cf": " ",
        "\u25aa": " ",
        "\u25e6": " ",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\t": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ ]+", " ", line).strip()
        lines.append(line)

    return "\n".join(lines)


def flatten_text(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(text)).strip()


def clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _soft_lines(text: str) -> List[str]:
    """Normalize spaces while preserving blank lines."""
    text = str(text or "")
    text = text.replace("\xa0", " ").replace("\t", " ")
    text = text.replace("\u2022", " ").replace("\u25cf", " ")
    text = text.replace("\u25aa", " ").replace("\u25e6", " ")

    return [
        re.sub(r"[ ]+", " ", line).strip()
        for line in text.splitlines()
    ]


# ============================================================
# SECTION DETECTION
# ============================================================

def _canonical_section(line: str) -> Optional[str]:
    if not line:
        return None

    cleaned = re.sub(r"[:|\-–—]+$", "", line.strip()).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)

    if len(cleaned) > 45:
        return None

    for section, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return section

    return None


def _extract_sections(text: str) -> Dict[str, List[str]]:
    """
    Split a resume into logical sections.
    Unknown content before the first recognized heading is kept as
    'header', which is useful for name/contact extraction.
    """
    lines = _soft_lines(text)

    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        section = _canonical_section(line)

        if section:
            current = section
            sections.setdefault(current, [])
            continue

        if line:
            sections.setdefault(current, []).append(line)

    return sections


# ============================================================
# EMAIL
# ============================================================

def _valid_email_username(username: str) -> bool:
    username = username.strip(" .,_-").lower()

    if len(username) < 3:
        return False

    if username in SKILL_SET:
        return False

    blocked = {
        "email", "mail", "gmail", "phone", "mobile", "contact",
        "skills", "education", "experience", "projects", "profile",
        "resume", "professional", "language", "programming",
        "database", "libraries", "tools", "computer", "science",
        "engineering", "data", "scientist", "developer"
    }

    if username in blocked:
        return False

    return bool(re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._%+-]*", username
    ))


def extract_email(text: str) -> Optional[str]:
    if not text:
        return None

    normalized = normalize_text(text)
    flat = flatten_text(text)

    # 1. Standard email.
    matches = EMAIL_PATTERN.findall(flat)
    valid = []

    for value in matches:
        email = re.sub(r"\s+", "", value).lower()
        username = email.split("@", 1)[0]

        if _valid_email_username(username):
            valid.append(email)

    if valid:
        # Prefer student-like addresses with digits, then longer
        # meaningful usernames.
        valid.sort(
            key=lambda e: (
                any(ch.isdigit() for ch in e.split("@")[0]),
                len(e.split("@")[0])
            ),
            reverse=True
        )
        return valid[0]

    # 2. PDF extraction may split the username and domain.
    # Example:
    #     bhaveshkeche22
    #     scikit-learn
    #     @gmail.com
    #
    # Search nearby candidates but reject skills/section words.
    domain_matches = list(re.finditer(
        r"@\s*([A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        flat,
        re.IGNORECASE
    ))

    candidates = []

    for match in domain_matches:
        domain = match.group(1).lower()
        before = flat[max(0, match.start() - 500):match.start()]

        words = re.findall(
            r"[A-Za-z0-9][A-Za-z0-9._%+-]{2,}",
            before
        )

        for word in words:
            username = word.strip(" .,_-")
            lower = username.lower()

            if not _valid_email_username(username):
                continue

            if lower in ALL_SECTION_HEADERS or lower in {
                "bhtech", "computer", "science", "engineering",
                "tableau", "scientist", "artificial",
                "intelligence", "machine", "learning"
            }:
                continue

            score = 0

            if any(ch.isdigit() for ch in username):
                score += 100
            if "_" in username or "." in username:
                score += 20
            if len(username) >= 8:
                score += 10

            # Prefer common email providers.
            if domain in {
                "gmail.com", "outlook.com", "hotmail.com",
                "yahoo.com", "protonmail.com"
            }:
                score += 10

            # Distance is useful but intentionally weak.
            score -= min(
                abs(len(before) - before.rfind(username)), 500
            ) * 0.02

            candidates.append((score, username, domain))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        _, username, domain = candidates[0]
        return f"{username}@{domain}".lower()

    # 3. Obfuscated form: user [at] domain [dot] com.
    obfuscated = re.search(
        r"([A-Za-z0-9._%+-]+)"
        r"\s*(?:\[at\]|\(at\)|\bat\b)"
        r"\s*([A-Za-z0-9.-]+)"
        r"\s*(?:\[dot\]|\(dot\)|\bdot\b)"
        r"\s*([A-Za-z]{2,})",
        flat,
        re.IGNORECASE
    )

    if obfuscated:
        username = obfuscated.group(1)
        if _valid_email_username(username):
            return (
                f"{username}@{obfuscated.group(2)}."
                f"{obfuscated.group(3)}"
            ).lower()

    # 4. Raw fallback.
    loose = re.search(
        r"[A-Za-z0-9._%+-]{3,}\s*@\s*"
        r"[A-Za-z0-9.-]{2,}\s*\.\s*[A-Za-z]{2,}",
        normalized.replace("\n", " "),
        re.IGNORECASE
    )

    if loose:
        email = re.sub(r"\s+", "", loose.group(0)).lower()
        if _valid_email_username(email.split("@", 1)[0]):
            return email

    return None


# ============================================================
# PHONE
# ============================================================

def extract_phone(text: str) -> Optional[str]:
    if not text:
        return None

    flat = flatten_text(text)

    for pattern in PHONE_PATTERNS:
        match = pattern.search(flat)
        if match:
            return match.group(0).strip()

    return None


# ============================================================
# NAME
# ============================================================

def _looks_like_name(line: str) -> bool:
    line = clean_spaces(line)

    if not line or len(line) > 60:
        return False

    lower = line.lower()

    ignored = {
        "resume", "curriculum vitae", "cv", "profile", "contact",
        "data scientist", "software engineer", "software developer",
        "developer", "education", "skills", "experience", "projects",
        "professional experience", "technical skills"
    }

    if lower in ignored:
        return False

    if "@" in line or re.search(r"\d{7,}", line):
        return False

    words = line.split()

    if not 2 <= len(words) <= 5:
        return False

    # Names are mostly alphabetic, with common surname punctuation.
    alpha = sum(ch.isalpha() for ch in line)
    allowed = sum(ch.isalpha() or ch in " .'-" for ch in line)

    if alpha < 4 or allowed != len(line):
        return False

    # A section-like line is not a name.
    if _canonical_section(line):
        return False

    return True


def extract_name(text: str) -> Optional[str]:
    if not text:
        return None

    sections = _extract_sections(text)

    # The header is the strongest signal.
    for line in sections.get("header", [])[:20]:
        if _looks_like_name(line):
            return line

    # Fallback: inspect first 15 normalized lines.
    for line in _soft_lines(text)[:15]:
        if _looks_like_name(line):
            return line

    return None


# ============================================================
# SKILLS
# ============================================================

def extract_skills(text: str) -> List[str]:
    if not text:
        return []

    flat = flatten_text(text).lower()
    found = []

    # Longest first avoids aliases creating duplicate entries.
    for skill in sorted(SKILL_LIST, key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, flat, re.IGNORECASE):
            canonical = skill.lower()

            if canonical not in found:
                found.append(canonical)

    # Normalize aliases.
    aliases = {
        "sklearn": "scikit-learn",
        "nodejs": "node.js",
        "large language model": "large language models",
    }

    normalized = []
    for skill in found:
        skill = aliases.get(skill, skill)
        if skill not in normalized:
            normalized.append(skill)

    return sorted(normalized)


# ============================================================
# EDUCATION
# ============================================================

def _contains_degree(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in DEGREE_PATTERNS
    )


def _is_education_line(line: str) -> bool:
    if not line:
        return False

    if _contains_degree(line):
        return True

    # Education records often contain these markers.
    if re.search(
        r"\b(?:cgpa|gpa|percentage|percent|marks|grade)\b",
        line,
        re.IGNORECASE
    ):
        return True

    if DATE_PATTERN.search(line):
        return True

    return False


def _group_education_records(lines: List[str]) -> List[str]:
    """
    Group consecutive education lines into records.
    A new degree keyword normally starts a new record.
    """
    records = []
    current = []

    for line in lines:
        if not line:
            if current:
                records.append(clean_spaces(" ".join(current)))
                current = []
            continue

        starts_new_degree = (
            bool(current)
            and _contains_degree(line)
        )

        if starts_new_degree:
            records.append(clean_spaces(" ".join(current)))
            current = [line]
        else:
            current.append(line)

    if current:
        records.append(clean_spaces(" ".join(current)))

    return records


def extract_education(text: str) -> str:
    if not text:
        return ""

    sections = _extract_sections(text)
    education_lines = sections.get("education", [])

    # Preferred path: an explicit Education section.
    if education_lines:
        records = _group_education_records(education_lines)

        # If grouping produced one large record, keep complete lines
        # instead of deleting useful institution/date information.
        return "\n".join(
            record for record in records if record
        )

    # Fallback for resumes without an Education heading.
    lines = _soft_lines(text)
    records = []
    current = []

    for line in lines:
        if _contains_degree(line):
            if current:
                records.append(clean_spaces(" ".join(current)))
            current = [line]
        elif current:
            # Include institution, dates, CGPA and percentage lines
            # until another major section is encountered.
            if _canonical_section(line):
                if current:
                    records.append(clean_spaces(" ".join(current)))
                current = []
            else:
                current.append(line)

    if current:
        records.append(clean_spaces(" ".join(current)))

    # Remove obviously unrelated records.
    useful = [
        r for r in records
        if _contains_degree(r)
    ]

    return "\n".join(useful)


# ============================================================
# EXPERIENCE
# ============================================================

def _clean_section_records(lines: List[str]) -> List[str]:
    """
    Preserve meaningful lines while removing accidental empty entries.
    """
    result = []
    for line in lines:
        line = clean_spaces(line)
        if line and line not in result:
            result.append(line)
    return result


def extract_experience(text: str) -> str:
    if not text:
        return ""

    sections = _extract_sections(text)
    lines = sections.get("experience", [])

    if not lines:
        return ""

    return "\n".join(_clean_section_records(lines))


# ============================================================
# PROJECTS
# ============================================================

def extract_projects(text: str) -> str:
    if not text:
        return ""

    sections = _extract_sections(text)
    lines = sections.get("projects", [])

    if not lines:
        return ""

    return "\n".join(_clean_section_records(lines))


# ============================================================
# OPTIONAL SECTION EXTRACTION
# ============================================================

def extract_certifications(text: str) -> str:
    sections = _extract_sections(text)
    return "\n".join(_clean_section_records(
        sections.get("certifications", [])
    ))


def extract_achievements(text: str) -> str:
    sections = _extract_sections(text)
    return "\n".join(_clean_section_records(
        sections.get("achievements", [])
    ))


def extract_summary(text: str) -> str:
    sections = _extract_sections(text)
    return "\n".join(_clean_section_records(
        sections.get("summary", [])
    ))


# ============================================================
# MAIN FUNCTION
# ============================================================

def extract_resume_information(text: str) -> Dict[str, object]:
    """
    Main public function.

    Returns:
        {
            "name": str | None,
            "email": str | None,
            "phone": str | None,
            "skills": list[str],
            "education": str,
            "experience": str,
            "projects": str,
            "certifications": str,
            "achievements": str,
            "summary": str
        }
    """
    result = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "projects": extract_projects(text),
        "certifications": extract_certifications(text),
        "achievements": extract_achievements(text),
        "summary": extract_summary(text),
    }

    print("\n========== RESUME INFORMATION ==========")
    for key, value in result.items():
        print(f"{key.title()}: {value}")
    print("========================================\n")

    return result


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    test_text = """
    Bhavesh Keche
    bhaveshkeche22
    Scikit-learn
    machine learning
    Python
    @gmail.com
    9356754170

    Education
    B-Tech (Computer Science & Engineering)
    P.R.Pote Patil College of Engineering & Managment
    08/2024 - 04/2028
    8.0 CGPA

    HSC (Science)
    Maharashtra State Board
    02/2024
    68.00 %

    SSC
    Maharashtra State Board
    03/2022
    72.80 %

    Skills
    artificial intelligence computer vision deep learning
    dsa generative ai github java keras llm machine learning
    matplotlib nlp numpy pandas power bi python pytorch rag
    scikit-learn seaborn sql tableau tensorflow

    Experience
    AI-ML & Deep Learning
    EduSkills Virtual - Internship

    Projects
    Number Recognition System using Machine Learning & Deep Learning
    AI Video Assistant (RAG + LLM)
    """

    data = extract_resume_information(test_text)

    assert data["name"] == "Bhavesh Keche"
    assert data["email"] == "bhaveshkeche22@gmail.com"
    assert data["phone"] == "9356754170"
    assert "B-Tech" in data["education"]
    assert "8.0 CGPA" in data["education"]
    assert "SSC" in data["education"]
    assert "HSC" in data["education"]
    assert "scikit-learn" in data["skills"]
    assert "AI-ML & Deep Learning" in data["experience"]
    assert "AI Video Assistant" in data["projects"]

    test_text_2 = """
    Priya Sharma
    priya.sharma91@yahoo.com
    9876543210

    Education
    Master of Computer Applications (MCA)
    Anna University
    2022 - 2024
    8.7 CGPA

    Bachelor of Science (Computer Science)
    St. Xavier's Institute of Technology
    2018 - 2021
    75.4 %

    12th Grade
    Central Board of Secondary Education
    2018
    89.2 %
    """

    data2 = extract_resume_information(test_text_2)

    assert "Anna University" in data2["education"]
    assert "MCA" in data2["education"]
    assert "8.7 CGPA" in data2["education"]
    assert "St. Xavier's Institute of Technology" in data2["education"]
    assert "Bachelor of Science" in data2["education"]

    print("ALL TESTS PASSED")
