from datetime import datetime
import os
import uuid
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename

from database.models import db, Resume, ExtractedData
from services.pdf_service import extract_text_from_pdf, preprocess_text
from services.resume_extractor import extract_resume_information
from services.quality_scorer import calculate_quality

resume = Blueprint("resume", __name__, url_prefix="/resume")
UPLOAD_FOLDER = os.path.join("uploads", "resumes")
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _serialize_information(info):
    return {
        "name": info.get("name"),
        "email": info.get("email"),
        "phone": info.get("phone"),
        "education": info.get("education", ""),
        "experience": info.get("experience", ""),
        "projects": info.get("projects", ""),
        "certifications": info.get("certifications", ""),
        "achievements": info.get("achievements", ""),
        "summary": info.get("summary", ""),
    }


@resume.post("/upload")
def upload_resume():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(success=False, message="Please login first."), 401
    if "resume" not in request.files:
        return jsonify(success=False, message="No resume file received."), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify(success=False, message="No file selected."), 400
    if not allowed_file(file.filename):
        return jsonify(success=False, message="Only PDF files are allowed."), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    original_filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    try:
        file.save(file_path)
        extracted_text = preprocess_text(extract_text_from_pdf(file_path))
        if not extracted_text:
            _remove_file(file_path)
            return jsonify(success=False, message="No readable text was found in the PDF. Scanned/image-only PDFs need OCR."), 400

        information = extract_resume_information(extracted_text)
        quality_score, quality_checks = calculate_quality(information, extracted_text)

        new_resume = Resume(
            user_id=user_id,
            filename=original_filename,
            extracted_text=extracted_text,
            uploaded_at=datetime.utcnow(),
            original_filename=original_filename,
            stored_filename=unique_name,
            file_path=file_path,
        )
        db.session.add(new_resume)
        db.session.flush()

        extracted = ExtractedData(
            resume_id=new_resume.id,
            name=information.get("name"),
            email=information.get("email"),
            phone=information.get("phone"),
            skills=", ".join(information.get("skills", [])),
            education=information.get("education", ""),
            projects=information.get("projects", ""),
            experience=information.get("experience", ""),
            certifications=information.get("certifications", ""),
            achievements=information.get("achievements", ""),
            summary=information.get("summary", ""),
        )
        db.session.add(extracted)
        db.session.commit()

        return jsonify(
            success=True,
            message="Resume uploaded and extracted successfully.",
            resume_id=new_resume.id,
            filename=original_filename,
            text_length=len(extracted_text),
            information=_serialize_information(information),
            skills=information.get("skills", []),
            quality_score=quality_score,
            quality_checks=quality_checks,
        )
    except Exception as error:
        db.session.rollback()
        _remove_file(file_path)
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f"Resume processing failed: {error}"), 500


@resume.get("/latest")
def latest_resume():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(success=False, message="Please login first."), 401
    item = Resume.query.filter_by(user_id=user_id).order_by(Resume.id.desc()).first()
    if not item:
        return jsonify(success=False, message="No resume uploaded yet."), 404
    info = extract_resume_information(item.extracted_text or "")
    quality_score, quality_checks = calculate_quality(info, item.extracted_text or "")
    return jsonify(success=True, resume_id=item.id, filename=item.original_filename or item.filename,
                   information=_serialize_information(info), skills=info.get("skills", []),
                   quality_score=quality_score, quality_checks=quality_checks)
