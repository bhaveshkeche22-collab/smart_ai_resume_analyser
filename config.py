import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "uploads/resumes"
    )

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    MAIL_PORT = int(
        os.getenv("MAIL_PORT", "587")
    )

    MAIL_USE_TLS = (
        os.getenv(
            "MAIL_USE_TLS",
            "True"
        ).lower() == "true"
    )

    MAIL_USE_SSL = (
        os.getenv(
            "MAIL_USE_SSL",
            "False"
        ).lower() == "true"
    )

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER"
    )