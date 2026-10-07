import json
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash
)

from database.models import (
    db,
    CareerRole,
    RoadmapStep,
    StudySubject,
    StudyTopic,
    DSAProblem,
    UserDSAProgress,
    InternshipOpportunity
)


learning = Blueprint(
    "learning",
    __name__,
    url_prefix="/learning"
)


def login_required():
    return "user_id" in session


@learning.route("/")
def index():

    if not login_required():
        flash(
            "Please login to access Learning Hub.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    roles = CareerRole.query.order_by(
        CareerRole.name
    ).all()

    subjects = StudySubject.query.order_by(
        StudySubject.name
    ).all()

    total_dsa = DSAProblem.query.count()

    completed_dsa = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        status="completed"
    ).count()

    saved_dsa = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        saved=True
    ).count()

    if total_dsa:
        dsa_progress = round(
            (completed_dsa / total_dsa) * 100
        )
    else:
        dsa_progress = 0

    internships = InternshipOpportunity.query.order_by(
        InternshipOpportunity.created_at.desc()
    ).limit(6).all()

    return render_template(
        "learning/index.html",
        roles=roles,
        subjects=subjects,
        total_dsa=total_dsa,
        completed_dsa=completed_dsa,
        saved_dsa=saved_dsa,
        dsa_progress=dsa_progress,
        internships=internships
    )


@learning.route("/roadmaps")
def roadmaps():

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    roles = CareerRole.query.order_by(
        CareerRole.name
    ).all()

    return render_template(
        "learning/roadmap.html",
        roles=roles
    )


@learning.route("/roadmap/<int:role_id>")
def roadmap_detail(role_id):

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    role = CareerRole.query.get_or_404(
        role_id
    )

    return render_template(
        "learning/roadmap.html",
        roles=[role],
        selected_role=role
    )


@learning.route("/study")
def study():

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    subjects = StudySubject.query.order_by(
        StudySubject.name
    ).all()

    return render_template(
        "learning/study.html",
        subjects=subjects
    )


@learning.route("/study/<int:subject_id>")
def subject_detail(subject_id):

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    subject = StudySubject.query.get_or_404(
        subject_id
    )

    return render_template(
        "learning/study.html",
        subjects=[subject],
        selected_subject=subject
    )


@learning.route("/dsa")
def dsa():

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    page = request.args.get(
        "page",
        1,
        type=int
    )

    search = request.args.get(
        "search",
        "",
        type=str
    ).strip()

    difficulty = request.args.get(
        "difficulty",
        "",
        type=str
    )

    topic = request.args.get(
        "topic",
        "",
        type=str
    )

    query = DSAProblem.query

    if search:
        query = query.filter(
            DSAProblem.title.ilike(
                f"%{search}%"
            )
        )

    if difficulty:
        query = query.filter_by(
            difficulty=difficulty
        )

    if topic:
        query = query.filter_by(
            topic=topic
        )

    pagination = query.order_by(
        DSAProblem.day_number,
        DSAProblem.id
    ).paginate(
        page=page,
        per_page=15,
        error_out=False
    )

    topics = db.session.query(
        DSAProblem.topic
    ).distinct().order_by(
        DSAProblem.topic
    ).all()

    topic_list = [
        item[0]
        for item in topics
        if item[0]
    ]

    progress_rows = UserDSAProgress.query.filter_by(
        user_id=session["user_id"]
    ).all()

    progress_map = {
        row.problem_id: row
        for row in progress_rows
    }

    return render_template(
        "learning/dsa.html",
        problems=pagination.items,
        pagination=pagination,
        progress_map=progress_map,
        topics=topic_list,
        current_search=search,
        current_difficulty=difficulty,
        current_topic=topic
    )


@learning.post("/dsa/<int:problem_id>/status")
def update_dsa_status(problem_id):

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    problem = DSAProblem.query.get_or_404(
        problem_id
    )

    status = request.form.get(
        "status",
        "not_started"
    )

    allowed = {
        "not_started",
        "in_progress",
        "completed",
        "revision"
    }

    if status not in allowed:
        return jsonify({
            "success": False,
            "message": "Invalid status"
        }), 400

    progress = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        problem_id=problem.id
    ).first()

    if not progress:

        progress = UserDSAProgress(
            user_id=session["user_id"],
            problem_id=problem.id
        )

        db.session.add(progress)

    progress.status = status

    if status == "completed":
        progress.completed_at = datetime.utcnow()
    else:
        progress.completed_at = None

    db.session.commit()

    return jsonify({
        "success": True,
        "status": status
    })


@learning.post("/dsa/<int:problem_id>/save")
def save_dsa(problem_id):

    if not login_required():
        return jsonify({
            "success": False
        }), 401

    problem = DSAProblem.query.get_or_404(
        problem_id
    )

    progress = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        problem_id=problem.id
    ).first()

    if not progress:

        progress = UserDSAProgress(
            user_id=session["user_id"],
            problem_id=problem.id
        )

        db.session.add(progress)

    progress.saved = not progress.saved

    db.session.commit()

    return jsonify({
        "success": True,
        "saved": progress.saved
    })


@learning.route("/internships")
def internships():

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    opportunities = InternshipOpportunity.query.order_by(
        InternshipOpportunity.name
    ).all()

    return render_template(
        "learning/internships.html",
        opportunities=opportunities
    )


@learning.route("/progress")
def progress():

    if not login_required():
        return redirect(
            url_for("auth.login")
        )

    total = DSAProblem.query.count()

    completed = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        status="completed"
    ).count()

    saved = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        saved=True
    ).count()

    in_progress = UserDSAProgress.query.filter_by(
        user_id=session["user_id"],
        status="in_progress"
    ).count()

    if total:
        percentage = round(
            completed / total * 100
        )
    else:
        percentage = 0

    return render_template(
        "learning/progress.html",
        total=total,
        completed=completed,
        saved=saved,
        in_progress=in_progress,
        percentage=percentage
    )