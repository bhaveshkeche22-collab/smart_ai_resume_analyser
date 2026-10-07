import json

from flask import Blueprint, jsonify, request, session

from database.models import (
    db,
    Resume,
    JobDescription,
    AnalysisResult
)

from services.resume_extractor import extract_resume_information
from services.ats_scorer import calculate_ats, build_recommendation
from services.gemini_service import (
    generate_recommendation,
    detect_missing_evidence
)
from services.quality_scorer import calculate_quality


analysis = Blueprint(
    "analysis",
    __name__,
    url_prefix="/analysis"
)


# ============================================================
# HELPERS
# ============================================================

def _get_resume(resume_id=None):

    user_id = session.get("user_id")

    if not user_id:
        return None, (
            jsonify(
                success=False,
                message="Please login first."
            ),
            401
        )

    query = Resume.query.filter_by(
        user_id=user_id
    )

    if resume_id:
        resume = query.filter_by(
            id=resume_id
        ).first()
    else:
        resume = (
            query
            .order_by(Resume.id.desc())
            .first()
        )

    if not resume:
        return None, (
            jsonify(
                success=False,
                message="Please upload a resume first."
            ),
            404
        )

    return resume, None


def _safe_json(value, default=None):

    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


def _analysis_payload(saved, job, resume):

    recommendation = _safe_json(
        saved.recommendations,
        {}
    )

    required_skills = _safe_json(
        job.required_skills,
        []
    )

    matched_skills = _safe_json(
        saved.matched_skills,
        []
    )

    missing_skills = _safe_json(
        saved.skill_gap,
        []
    )

    matched_keywords = _safe_json(
        saved.matched_keywords,
        []
    )

    description = job.description or ""

    experience_level = ""

    if description.startswith(
        "Experience level:"
    ):

        first_line, _, remaining = description.partition("\n")

        experience_level = (
            first_line
            .replace(
                "Experience level:",
                ""
            )
            .strip()
        )

        job_description = remaining.strip()

    else:

        job_description = description

    return {

        # ----------------------------------------------------
        # BASIC IDENTIFIERS
        # ----------------------------------------------------

        "analysis_id": saved.id,

        "resume_id": resume.id,

        "job_id": job.id,

        "job_title": job.job_title,

        "experience_level": experience_level,


        # ----------------------------------------------------
        # IMPORTANT SOURCE DATA
        # These are required by the Improvement Studio
        # ----------------------------------------------------

        "resume_text": (
            resume.extracted_text or ""
        ),

        "job_description": job_description,


        # ----------------------------------------------------
        # ATS SCORES
        # ----------------------------------------------------

        "ats_score": saved.ats_score or 0,

        "match_score": saved.match_score or 0,

        "skill_match_score": saved.match_score or 0,

        "similarity_score": (
            saved.similarity_score or 0
        ),

        "education_score": (
            saved.education_score or 0
        ),

        "project_score": (
            saved.project_score or 0
        ),

        "experience_score": (
            saved.experience_score or 0
        ),

        "keyword_score": (
            saved.keyword_score or 0
        ),

        "quality_score": (
            saved.quality_score or 0
        ),


        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "matched_keywords": matched_keywords,


        # ----------------------------------------------------
        # RECOMMENDATION
        # ----------------------------------------------------

        "recommendation": recommendation,


        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        "created_at": (
            saved.created_at.isoformat()
            if saved.created_at
            else None
        )
    }


# ============================================================
# ANALYZE RESUME
# ============================================================

@analysis.post("/analyze")
def analyze():

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        # ----------------------------------------------------
        # GET RESUME
        # ----------------------------------------------------

        resume, error = _get_resume(
            data.get("resume_id")
        )

        if error:
            return error


        # ----------------------------------------------------
        # GET JOB DATA
        # ----------------------------------------------------

        job_title = str(
            data.get("job_title")
            or ""
        ).strip()

        experience_level = str(
            data.get("experience_level")
            or ""
        ).strip()

        job_description = str(
            data.get("job_description")
            or ""
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not job_title:

            return jsonify(
                success=False,
                message="Please select a target job."
            ), 400


        if len(job_description) < 30:

            return jsonify(
                success=False,
                message=(
                    "Please enter a complete job "
                    "description (at least 30 characters)."
                )
            ), 400


        resume_text = (
            resume.extracted_text
            or ""
        ).strip()


        if not resume_text:

            return jsonify(
                success=False,
                message=(
                    "Resume text could not be extracted."
                )
            ), 400


        # ----------------------------------------------------
        # EXTRACT RESUME INFORMATION
        # ----------------------------------------------------

        information = extract_resume_information(
            resume_text
        )


        # ----------------------------------------------------
        # ATS CALCULATION
        # ----------------------------------------------------

        result = calculate_ats(
            information,
            resume_text,
            job_description
        )


        # ----------------------------------------------------
        # QUALITY SCORE
        # ----------------------------------------------------

        quality_score, quality_details = (
            calculate_quality(
                information,
                resume_text
            )
        )


        # ----------------------------------------------------
        # LOCAL RECOMMENDATION
        # ----------------------------------------------------

        recommendation = build_recommendation(
            result,
            information
        )


        # ----------------------------------------------------
        # GEMINI RECOMMENDATION
        # ----------------------------------------------------

        try:

            ai_recommendation = (
                generate_recommendation(
                    resume_text,
                    job_description,
                    result
                )
            )

            if (
                isinstance(
                    ai_recommendation,
                    dict
                )
                and ai_recommendation.get(
                    "provider"
                ) == "gemini"
            ):

                recommendation = (
                    ai_recommendation
                )

        except Exception as gemini_error:

            print(
                "Gemini recommendation error:",
                gemini_error
            )


        # ----------------------------------------------------
        # SAVE JOB DESCRIPTION
        # ----------------------------------------------------

        job = JobDescription(

            job_title=job_title,

            description=(
                f"Experience level: "
                f"{experience_level}\n"
                f"{job_description}"
            ).strip(),

            required_skills=json.dumps(
                result.get(
                    "required_skills",
                    []
                )
            )
        )

        db.session.add(job)

        db.session.flush()


        # ----------------------------------------------------
        # SAVE ANALYSIS
        # ----------------------------------------------------

        saved = AnalysisResult(

            resume_id=resume.id,

            job_id=job.id,

            ats_score=result.get(
                "ats_score",
                0
            ),

            match_score=result.get(
                "skill_match_score",
                0
            ),

            similarity_score=result.get(
                "similarity_score",
                0
            ),

            education_score=result.get(
                "education_score",
                0
            ),

            project_score=result.get(
                "project_score",
                0
            ),

            experience_score=result.get(
                "experience_score",
                0
            ),

            keyword_score=result.get(
                "keyword_score",
                0
            ),

            quality_score=quality_score,

            skill_gap=json.dumps(
                result.get(
                    "missing_skills",
                    []
                )
            ),

            matched_skills=json.dumps(
                result.get(
                    "matched_skills",
                    []
                )
            ),

            matched_keywords=json.dumps(
                result.get(
                    "matched_keywords",
                    []
                )
            ),

            recommendations=json.dumps(
                recommendation
            )
        )

        db.session.add(saved)

        db.session.commit()


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        payload = _analysis_payload(
            saved,
            job,
            resume
        )

        payload["success"] = True

        # Extra information for frontend
        payload["resume_information"] = information

        payload["quality_details"] = (
            quality_details
        )

        return jsonify(payload), 200


    except Exception as error:

        db.session.rollback()

        print(
            "\n========== ANALYSIS ERROR =========="
        )

        print(error)

        import traceback

        traceback.print_exc()

        print(
            "====================================\n"
        )

        return jsonify(
            success=False,
            message="Analysis failed.",
            error=str(error)
        ), 500


# ============================================================
# LATEST ANALYSIS
# ============================================================

@analysis.get("/latest")
def latest():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return jsonify(
            success=False,
            message="Please login first."
        ), 401


    saved = (
        AnalysisResult.query

        .join(Resume)

        .filter(
            Resume.user_id == user_id
        )

        .order_by(
            AnalysisResult.id.desc()
        )

        .first()
    )


    if not saved:

        return jsonify(
            success=False,
            message="No analysis found."
        ), 404


    return jsonify(
        success=True,
        **_analysis_payload(
            saved,
            saved.job,
            saved.resume
        )
    )


# ============================================================
# ANALYSIS HISTORY
# ============================================================

@analysis.get("/history")
def history():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return jsonify(
            success=False,
            message="Please login first."
        ), 401


    rows = (
        db.session.query(
            AnalysisResult,
            JobDescription
        )

        .join(
            JobDescription,
            AnalysisResult.job_id
            == JobDescription.id
        )

        .join(
            Resume,
            AnalysisResult.resume_id
            == Resume.id
        )

        .filter(
            Resume.user_id == user_id
        )

        .order_by(
            AnalysisResult.id.desc()
        )

        .limit(10)

        .all()
    )


    items = []


    for item, job in rows:

        items.append({

            "analysis_id": item.id,

            "resume_id": item.resume_id,

            "job_title": job.job_title,

            "ats_score": (
                item.ats_score or 0
            ),

            "match_score": (
                item.match_score or 0
            ),

            "similarity_score": (
                item.similarity_score or 0
            ),

            "quality_score": (
                item.quality_score or 0
            ),

            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else None
            )
        })


    return jsonify(
        success=True,
        analyses=items
    )


# ============================================================
# MISSING EVIDENCE DETECTOR
# ============================================================

@analysis.post("/evidence-check")
def evidence_check():

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        # ----------------------------------------------------
        # FIRST TRY DATA SENT BY FRONTEND
        # ----------------------------------------------------

        resume_text = str(
            data.get(
                "resume_text"
            )
            or ""
        ).strip()


        job_description = str(
            data.get(
                "job_description"
            )
            or ""
        ).strip()


        missing_skills = (
            data.get(
                "missing_skills"
            )
            or []
        )


        # ----------------------------------------------------
        # IF FRONTEND DID NOT SEND DATA,
        # LOAD LATEST ANALYSIS FROM DATABASE
        # ----------------------------------------------------

        if (
            not resume_text
            or not job_description
            or not missing_skills
        ):

            user_id = session.get(
                "user_id"
            )

            if not user_id:

                return jsonify(
                    success=False,
                    message="Please login first."
                ), 401


            saved = (
                AnalysisResult.query

                .join(Resume)

                .filter(
                    Resume.user_id == user_id
                )

                .order_by(
                    AnalysisResult.id.desc()
                )

                .first()
            )


            if saved:

                resume = saved.resume

                job = saved.job


                if not resume_text:

                    resume_text = (
                        resume.extracted_text
                        or ""
                    ).strip()


                if not job_description:

                    description = (
                        job.description
                        or ""
                    )

                    if description.startswith(
                        "Experience level:"
                    ):

                        _, _, description = (
                            description.partition(
                                "\n"
                            )
                        )

                    job_description = (
                        description.strip()
                    )


                if not missing_skills:

                    missing_skills = (
                        _safe_json(
                            saved.skill_gap,
                            []
                        )
                    )


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not resume_text:

            return jsonify(
                success=False,
                message=(
                    "Resume text is missing. "
                    "Please upload and analyze "
                    "your resume first."
                )
            ), 400


        if not job_description:

            return jsonify(
                success=False,
                message=(
                    "Job description is missing. "
                    "Please analyze a resume "
                    "against a job description first."
                )
            ), 400


        if not isinstance(
            missing_skills,
            list
        ):

            return jsonify(
                success=False,
                message=(
                    "Missing skills must be a list."
                )
            ), 400


        # ----------------------------------------------------
        # NO MISSING SKILLS
        # ----------------------------------------------------

        if not missing_skills:

            return jsonify({

                "success": True,

                "provider": "local",

                "message": (
                    "No missing skills were "
                    "found in the current analysis."
                ),

                "evidence": [],

                "missing_skills": []

            }), 200


        # ----------------------------------------------------
        # GEMINI / EVIDENCE ANALYSIS
        # ----------------------------------------------------

        result = detect_missing_evidence(

            resume_text=resume_text,

            job_description=job_description,

            missing_skills=missing_skills

        )


        # Make sure frontend always receives success
        if not isinstance(
            result,
            dict
        ):

            result = {

                "success": True,

                "provider": "local",

                "evidence": result

            }


        result.setdefault(
            "success",
            True
        )

        result.setdefault(
            "missing_skills",
            missing_skills
        )


        return jsonify(
            result
        ), 200


    except Exception as error:

        print(
            "\n========== EVIDENCE ERROR =========="
        )

        print(error)

        import traceback

        traceback.print_exc()

        print(
            "====================================\n"
        )


        return jsonify({

            "success": False,

            "message": (
                "Unable to analyze "
                "skill evidence."
            ),

            "error": str(error)

        }), 500