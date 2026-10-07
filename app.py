import os

from flask import (
    Flask,
    jsonify,
    render_template
)

from config import Config

from database.models import db

from database.migrate import ensure_schema

from extensions import mail

from routes.auth import auth
from routes.resume import resume
from routes.analysis import analysis
from routes.jobs import jobs
from routes.learning import learning



app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

app.config.from_object(Config)


# =========================================================
# DATABASE
# =========================================================

db.init_app(app)


# =========================================================
# EMAIL
# =========================================================

mail.init_app(app)
print("MAIL SERVER:", app.config.get("MAIL_SERVER"))
print("MAIL USERNAME:", app.config.get("MAIL_USERNAME"))
print("MAIL DEFAULT SENDER:", app.config.get("MAIL_DEFAULT_SENDER"))

# =========================================================
# REGISTER BLUEPRINTS
# =========================================================

app.register_blueprint(auth)

app.register_blueprint(resume)

app.register_blueprint(analysis)

app.register_blueprint(jobs)

app.register_blueprint(learning)
# =========================================================
# PUBLIC HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return jsonify(
        success=True,
        service="AI Resume Analyzer"
    )


# =========================================================
# INITIALIZE APPLICATION
# =========================================================

with app.app_context():

    # Upload directory
    upload_folder = app.config.get(
        "UPLOAD_FOLDER",
        "uploads/resumes"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    # Database schema
    ensure_schema(db)

import json

@app.template_filter("fromjson")
def fromjson_filter(value):

    if not value:
        return []

    try:
        return json.loads(value)

    except Exception:
        return []
# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )