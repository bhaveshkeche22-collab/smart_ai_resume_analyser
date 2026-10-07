import random
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)

from flask_mail import Message

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.models import db, User
from extensions import mail


auth = Blueprint("auth", __name__)


# =========================================================
# HELPER - GENERATE OTP
# =========================================================

def generate_otp():
    """
    Generate a secure 6-digit OTP.
    """
    return str(random.randint(100000, 999999))


# =========================================================
# HELPER - SEND OTP EMAIL
# =========================================================

def send_otp_email(user):
    sender = current_app.config.get("MAIL_USERNAME")

    if not sender:
        raise Exception("MAIL_USERNAME is not configured.")

    msg = Message(
        subject="AI Resume Analyzer - Email Verification",
        sender=sender,
        recipients=[user.email]
    )

    msg.body = f"""Hello {user.username},

Welcome to AI Resume Analyzer!

Your email verification OTP is:

{user.otp_code}

This OTP is valid for 5 minutes.

You have a maximum of 5 verification attempts.

If you did not create this account, please ignore this email.

Regards,
AI Resume Analyzer Team
"""

    mail.send(msg)

# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    # If already logged in
    if "user_id" in session:
        return redirect(
            url_for("auth.dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not username or not email or not password:

            flash(
                "Please fill in all required fields.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # -------------------------------------------------
        # PASSWORD CONFIRMATION
        # -------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # -------------------------------------------------
        # PASSWORD LENGTH
        # -------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # -------------------------------------------------
        # CHECK EXISTING EMAIL
        # -------------------------------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            # If account exists but is not verified,
            # allow user to continue verification.
            if not existing_user.is_verified:

                otp = generate_otp()

                existing_user.otp_code = otp

                existing_user.otp_expires_at = (
                    datetime.utcnow()
                    + timedelta(minutes=5)
                )

                existing_user.otp_attempts = 0

                db.session.commit()

                try:

                    send_otp_email(
                        existing_user
                    )

                except Exception as e:

                    print(
                        "EMAIL ERROR:",
                        e
                    )

                    flash(
                        "Unable to send verification email. Check your email configuration.",
                        "danger"
                    )

                    return redirect(
                        url_for("auth.register")
                    )

                session[
                    "verification_user_id"
                ] = existing_user.id

                flash(
                    "A new OTP has been sent to your email.",
                    "info"
                )

                return redirect(
                    url_for("auth.verify_otp")
                )

            flash(
                "An account with this email already exists.",
                "warning"
            )

            return redirect(
                url_for("auth.register")
            )

        # -------------------------------------------------
        # GENERATE OTP
        # -------------------------------------------------

        otp = generate_otp()

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        new_user = User(

            username=username,

            email=email,

            password_hash=generate_password_hash(
                password
            ),

            is_verified=False,

            otp_code=otp,

            otp_expires_at=(
                datetime.utcnow()
                + timedelta(minutes=5)
            ),

            otp_attempts=0
        )

        db.session.add(
            new_user
        )

        db.session.commit()

        # -------------------------------------------------
        # SEND OTP EMAIL
        # -------------------------------------------------

        try:

            send_otp_email(
                new_user
            )

        except Exception as e:

            print(
                "EMAIL ERROR:",
                e
            )

            db.session.delete(
                new_user
            )

            db.session.commit()

            flash(
                "Unable to send verification email. Please check your email configuration.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # -------------------------------------------------
        # SAVE VERIFICATION SESSION
        # -------------------------------------------------

        session[
            "verification_user_id"
        ] = new_user.id

        flash(
            "Registration successful! We sent a verification OTP to your email.",
            "success"
        )

        return redirect(
            url_for("auth.verify_otp")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# VERIFY OTP
# =========================================================

@auth.route(
    "/verify-otp",
    methods=["GET", "POST"]
)
def verify_otp():

    user_id = session.get(
        "verification_user_id"
    )

    # -----------------------------------------------------
    # NO VERIFICATION SESSION
    # -----------------------------------------------------

    if not user_id:

        flash(
            "Verification session expired. Please register again.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    user = User.query.get(
        user_id
    )

    # -----------------------------------------------------
    # USER NOT FOUND
    # -----------------------------------------------------

    if not user:

        session.pop(
            "verification_user_id",
            None
        )

        flash(
            "User account not found.",
            "danger"
        )

        return redirect(
            url_for("auth.register")
        )

    # -----------------------------------------------------
    # ALREADY VERIFIED
    # -----------------------------------------------------

    if user.is_verified:

        session.pop(
            "verification_user_id",
            None
        )

        flash(
            "Email is already verified. Please login.",
            "info"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        otp = request.form.get(
            "otp",
            ""
        ).strip()

        # -------------------------------------------------
        # EMPTY OTP
        # -------------------------------------------------

        if not otp:

            flash(
                "Please enter the OTP.",
                "danger"
            )

            return redirect(
                url_for("auth.verify_otp")
            )

        # -------------------------------------------------
        # OTP FORMAT
        # -------------------------------------------------

        if not otp.isdigit() or len(otp) != 6:

            flash(
                "OTP must contain exactly 6 digits.",
                "danger"
            )

            return redirect(
                url_for("auth.verify_otp")
            )

        # -------------------------------------------------
        # MAX ATTEMPTS
        # -------------------------------------------------

        if user.otp_attempts >= 5:

            flash(
                "Too many incorrect attempts. Please request a new OTP.",
                "danger"
            )

            return redirect(
                url_for("auth.verify_otp")
            )

        # -------------------------------------------------
        # CHECK EXPIRY
        # -------------------------------------------------

        if (
            not user.otp_expires_at
            or datetime.utcnow()
            > user.otp_expires_at
        ):

            flash(
                "Your OTP has expired. Please request a new OTP.",
                "warning"
            )

            return redirect(
                url_for("auth.verify_otp")
            )

        # -------------------------------------------------
        # CHECK OTP
        # -------------------------------------------------

        if otp != user.otp_code:

            user.otp_attempts += 1

            db.session.commit()

            remaining = 5 - user.otp_attempts

            flash(
                f"Invalid OTP. {remaining} attempt(s) remaining.",
                "danger"
            )

            return redirect(
                url_for("auth.verify_otp")
            )

        # -------------------------------------------------
        # SUCCESSFUL VERIFICATION
        # -------------------------------------------------

        user.is_verified = True

        user.otp_code = None

        user.otp_expires_at = None

        user.otp_attempts = 0

        db.session.commit()

        # Remove temporary verification session
        session.pop(
            "verification_user_id",
            None
        )

        flash(
            "Email verified successfully! You can now login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "verify_otp.html",
        email=user.email
    )


# =========================================================
# RESEND OTP
# =========================================================

@auth.route(
    "/resend-otp",
    methods=["POST"]
)
def resend_otp():

    user_id = session.get(
        "verification_user_id"
    )

    if not user_id:

        flash(
            "Verification session expired. Please register again.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    user = User.query.get(
        user_id
    )

    if not user:

        session.pop(
            "verification_user_id",
            None
        )

        flash(
            "User account not found.",
            "danger"
        )

        return redirect(
            url_for("auth.register")
        )

    if user.is_verified:

        session.pop(
            "verification_user_id",
            None
        )

        flash(
            "Your email is already verified.",
            "info"
        )

        return redirect(
            url_for("auth.login")
        )

    # Generate new OTP
    otp = generate_otp()

    user.otp_code = otp

    user.otp_expires_at = (
        datetime.utcnow()
        + timedelta(minutes=5)
    )

    user.otp_attempts = 0

    db.session.commit()

    # Send email
    try:

        send_otp_email(
            user
        )

    except Exception as e:

        print(
            "RESEND EMAIL ERROR:",
            e
        )

        flash(
            "Unable to send OTP. Please check email configuration.",
            "danger"
        )

        return redirect(
            url_for("auth.verify_otp")
        )

    flash(
        "A new OTP has been sent to your email.",
        "success"
    )

    return redirect(
        url_for("auth.verify_otp")
    )


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if "user_id" in session:

        return redirect(
            url_for("auth.dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        # -------------------------------------------------
        # CHECK EMAIL + PASSWORD
        # -------------------------------------------------

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            # -------------------------------------------------
            # EMAIL NOT VERIFIED
            # -------------------------------------------------

            if not user.is_verified:

                # Generate fresh OTP
                otp = generate_otp()

                user.otp_code = otp

                user.otp_expires_at = (
                    datetime.utcnow()
                    + timedelta(minutes=5)
                )

                user.otp_attempts = 0

                db.session.commit()

                # Send OTP
                try:

                    send_otp_email(
                        user
                    )

                except Exception as e:

                    print(
                        "LOGIN OTP EMAIL ERROR:",
                        e
                    )

                    flash(
                        "Unable to send verification email. Please try again.",
                        "danger"
                    )

                    return render_template(
                        "login.html"
                    )

                session[
                    "verification_user_id"
                ] = user.id

                flash(
                    "Your email is not verified. A new OTP has been sent.",
                    "warning"
                )

                return redirect(
                    url_for("auth.verify_otp")
                )

            # -------------------------------------------------
            # VERIFIED USER
            # -------------------------------------------------

            session.clear()

            session["user_id"] = user.id

            session["username"] = user.username

            session["email"] = user.email

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("auth.dashboard")
            )

        # -------------------------------------------------
        # INVALID LOGIN
        # -------------------------------------------------

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@auth.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        flash(
            "Please login to access the dashboard.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "dashboard.html",
        username=session.get(
            "username"
        ),
        email=session.get(
            "email"
        )
    )


# =========================================================
# CURRENT USER API
# =========================================================

@auth.get("/me")
def current_user():

    if "user_id" not in session:

        return {
            "success": False,
            "authenticated": False,
            "message": "Please login first."
        }, 401

    user = User.query.get(
        session["user_id"]
    )

    if not user:

        session.clear()

        return {
            "success": False,
            "authenticated": False,
            "message": "User account not found."
        }, 404

    return {
        "success": True,
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            )
        }
    }


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("home")
    )