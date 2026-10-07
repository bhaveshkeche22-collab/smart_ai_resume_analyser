from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


# =========================================================
# USER
# =========================================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # =====================================================
    # EMAIL VERIFICATION
    # =====================================================

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    otp_code = db.Column(
        db.String(6),
        nullable=True
    )

    otp_expires_at = db.Column(
        db.DateTime,
        nullable=True
    )

    otp_attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    resumes = db.relationship(
        "Resume",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================================================
# RESUME
# =========================================================

class Resume(db.Model):

    __tablename__ = "resumes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    extracted_text = db.Column(
        db.Text,
        nullable=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    original_filename = db.Column(
        db.String(255),
        nullable=True
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=True
    )

    file_path = db.Column(
        db.String(500),
        nullable=True
    )

    user = db.relationship(
        "User",
        back_populates="resumes"
    )

    extracted_data = db.relationship(
        "ExtractedData",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan"
    )

    analyses = db.relationship(
        "AnalysisResult",
        back_populates="resume",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================================================
# EXTRACTED DATA
# =========================================================

class ExtractedData(db.Model):

    __tablename__ = "extracted_data"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resume_id = db.Column(
        db.Integer,
        db.ForeignKey("resumes.id"),
        nullable=False,
        unique=True
    )

    name = db.Column(
        db.String(150)
    )

    email = db.Column(
        db.String(150)
    )

    phone = db.Column(
        db.String(30)
    )

    skills = db.Column(
        db.Text
    )

    education = db.Column(
        db.Text
    )

    projects = db.Column(
        db.Text
    )

    experience = db.Column(
        db.Text
    )

    certifications = db.Column(
        db.Text
    )

    achievements = db.Column(
        db.Text
    )

    summary = db.Column(
        db.Text
    )

    resume = db.relationship(
        "Resume",
        back_populates="extracted_data"
    )


# =========================================================
# JOB DESCRIPTION
# =========================================================

class JobDescription(db.Model):

    __tablename__ = "job_descriptions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    job_title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    required_skills = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    analysis_results = db.relationship(
        "AnalysisResult",
        back_populates="job",
        lazy=True
    )


# =========================================================
# ANALYSIS RESULT
# =========================================================

class AnalysisResult(db.Model):

    __tablename__ = "analysis_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resume_id = db.Column(
        db.Integer,
        db.ForeignKey("resumes.id"),
        nullable=False
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("job_descriptions.id"),
        nullable=False
    )

    ats_score = db.Column(
        db.Float,
        nullable=True
    )

    match_score = db.Column(
        db.Float,
        nullable=True
    )

    similarity_score = db.Column(
        db.Float,
        nullable=True
    )

    education_score = db.Column(
        db.Float,
        nullable=True
    )

    project_score = db.Column(
        db.Float,
        nullable=True
    )

    experience_score = db.Column(
        db.Float,
        nullable=True
    )

    keyword_score = db.Column(
        db.Float,
        nullable=True
    )

    quality_score = db.Column(
        db.Float,
        nullable=True
    )

    skill_gap = db.Column(
        db.Text,
        nullable=True
    )

    matched_skills = db.Column(
        db.Text,
        nullable=True
    )

    matched_keywords = db.Column(
        db.Text,
        nullable=True
    )

    recommendations = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    resume = db.relationship(
        "Resume",
        back_populates="analyses"
    )

    job = db.relationship(
        "JobDescription",
        back_populates="analysis_results"
    )

class CareerRole(db.Model):
    __tablename__ = "career_roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roadmap_steps = db.relationship(
        "RoadmapStep",
        back_populates="career_role",
        cascade="all, delete-orphan",
        order_by="RoadmapStep.step_number"
    )


class RoadmapStep(db.Model):
    __tablename__ = "roadmap_steps"

    id = db.Column(db.Integer, primary_key=True)
    career_role_id = db.Column(
        db.Integer,
        db.ForeignKey("career_roles.id"),
        nullable=False
    )

    step_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    topics = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.String(100), nullable=True)

    career_role = db.relationship(
        "CareerRole",
        back_populates="roadmap_steps"
    )


class StudySubject(db.Model):
    __tablename__ = "study_subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    material_path = db.Column(db.String(500), nullable=True)

    topics = db.relationship(
        "StudyTopic",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="StudyTopic.order_number"
    )


class StudyTopic(db.Model):
    __tablename__ = "study_topics"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("study_subjects.id"),
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_number = db.Column(db.Integer, default=0)

    subject = db.relationship(
        "StudySubject",
        back_populates="topics"
    )


class DSAProblem(db.Model):
    __tablename__ = "dsa_problems"

    id = db.Column(db.Integer, primary_key=True)

    day_number = db.Column(db.Integer, nullable=True)
    topic = db.Column(db.String(150), nullable=True)

    title = db.Column(db.String(255), nullable=False)

    difficulty = db.Column(
        db.String(30),
        nullable=True
    )

    estimated_time = db.Column(
        db.String(50),
        nullable=True
    )

    article_url = db.Column(
        db.String(1000),
        nullable=True
    )

    youtube_url = db.Column(
        db.String(1000),
        nullable=True
    )

    practice_url = db.Column(
        db.String(1000),
        nullable=True
    )

    companies = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class UserDSAProgress(db.Model):
    __tablename__ = "user_dsa_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("dsa_problems.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="not_started"
    )

    saved = db.Column(
        db.Boolean,
        default=False
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user = db.relationship("User")

    problem = db.relationship("DSAProblem")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "problem_id",
            name="unique_user_problem"
        ),
    )


class InternshipOpportunity(db.Model):
    __tablename__ = "internship_opportunities"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(200),
        nullable=False
    )

    organization = db.Column(
        db.String(200),
        nullable=True
    )

    opportunity_type = db.Column(
        db.String(100),
        nullable=True
    )

    eligibility = db.Column(
        db.Text,
        nullable=True
    )

    period = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    official_url = db.Column(
        db.String(1000),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )