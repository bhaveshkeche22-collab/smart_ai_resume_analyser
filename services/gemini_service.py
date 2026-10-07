import json
import os
import urllib.error
import urllib.request


def generate_recommendation(resume_text, job_description, ats_result):
    """Use Gemini when configured; otherwise return a deterministic local recommendation."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    fallback = {
        "summary": "Analysis completed using the local ATS engine.",
        "suggestions": [],
    }

    missing = ats_result.get("missing_skills", [])
    if missing:
        fallback["suggestions"].append(
            "Add truthful evidence for these missing skills where you actually have them: "
            + ", ".join(missing[:10]) + "."
        )
    if ats_result.get("keyword_score", 0) < 60:
        fallback["suggestions"].append(
            "Add relevant keywords from the job description naturally to your summary, projects, and experience."
        )
    if ats_result.get("similarity_score", 0) < 50:
        fallback["suggestions"].append(
            "Rewrite project and experience bullets to describe responsibilities and technologies that overlap with the target role."
        )
    if not fallback["suggestions"]:
        fallback["suggestions"].append(
            "Keep the resume concise, quantify achievements, and tailor the strongest evidence to the target job."
        )

    if not api_key:
        return fallback

    prompt = f"""You are a resume reviewer. Give concise, factual recommendations based only on the supplied resume and job description.
Return valid JSON with exactly two keys: summary (string) and suggestions (array of strings).
Do not invent qualifications or achievements.

ATS result:
{json.dumps(ats_result, indent=2)}

Resume:
{resume_text[:12000]}

Job description:
{job_description[:10000]}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }).encode("utf-8")

    try:
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("suggestions"), list):
            return {
                "summary": str(parsed.get("summary") or fallback["summary"]),
                "suggestions": [str(x) for x in parsed["suggestions"][:8]],
                "provider": "gemini",
            }
    except Exception:
        pass

    fallback["provider"] = "local"
    return fallback
import os
import json
import re


def detect_missing_evidence(resume_text, job_description, missing_skills):
    """
    Detect whether missing JD skills have actual evidence in the resume.

    Important:
    - Never invent skills.
    - Never recommend falsely adding a skill.
    - A skill is considered supported only when there is reasonable
      evidence in the resume text.
    """

    if not resume_text:
        return {
            "success": False,
            "evidence": []
        }

    if not job_description:
        return {
            "success": False,
            "evidence": []
        }

    if not missing_skills:
        return {
            "success": True,
            "evidence": []
        }

    api_key = os.getenv("GEMINI_API_KEY")

    # -------------------------------------------------
    # FALLBACK WITHOUT GEMINI
    # -------------------------------------------------

    if not api_key:
        return _fallback_evidence_check(
            resume_text,
            missing_skills
        )

    try:

        import google.generativeai as genai

        genai.configure(
            api_key=api_key
        )

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        skills_text = ", ".join(
            str(skill)
            for skill in missing_skills
        )

        prompt = f"""
You are a resume evidence analysis engine.

Your task is NOT to invent information.

Analyze the resume and job description below.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

MISSING JOB SKILLS:
{skills_text}

For every missing skill determine whether the resume
contains actual evidence of using that technology or skill.

Possible status:

1. "missing"
   No evidence found.

2. "indirect"
   Related knowledge exists, but direct evidence is weak.

3. "supported"
   Resume contains reasonable evidence that the candidate
   has actually used the skill.

IMPORTANT:
Do not assume that a skill is known merely because a related
technology appears.

For example:
AWS must not be marked supported simply because Python
appears.

Return ONLY valid JSON.

Format:

{{
    "evidence": [
        {{
            "skill": "AWS",
            "status": "missing",
            "confidence": 0.95,
            "evidence": "",
            "recommendation": "Only add AWS if you have actually used it."
        }}
    ]
}}

No markdown.
No explanation outside JSON.
"""

        response = model.generate_content(
            prompt
        )

        raw = response.text.strip()

        # Remove accidental markdown fences
        raw = re.sub(
            r"```json|```",
            "",
            raw,
            flags=re.IGNORECASE
        ).strip()

        result = json.loads(raw)

        if not isinstance(result, dict):
            raise ValueError(
                "Invalid Gemini response"
            )

        if "evidence" not in result:
            result["evidence"] = []

        return {
            "success": True,
            "evidence": result["evidence"]
        }

    except Exception as error:

        print(
            "Evidence detection Gemini error:",
            error
        )

        return _fallback_evidence_check(
            resume_text,
            missing_skills
        )


# =====================================================
# FALLBACK EVIDENCE CHECK
# =====================================================

def _fallback_evidence_check(
    resume_text,
    missing_skills
):

    resume_lower = resume_text.lower()

    evidence = []

    for skill in missing_skills:

        skill_text = str(skill).strip()

        if not skill_text:
            continue

        if skill_text.lower() in resume_lower:

            evidence.append({
                "skill": skill_text,
                "status": "supported",
                "confidence": 0.70,
                "evidence": (
                    "The skill appears in the resume text."
                ),
                "recommendation": (
                    "Verify that your resume contains "
                    "a project, internship, or work example "
                    "showing how you used this skill."
                )
            })

        else:

            evidence.append({
                "skill": skill_text,
                "status": "missing",
                "confidence": 0.90,
                "evidence": "",
                "recommendation": (
                    f"Only add {skill_text} if you have "
                    "actually used it in a project, course, "
                    "internship, or professional experience."
                )
            })

    return {
        "success": True,
        "evidence": evidence
    }

