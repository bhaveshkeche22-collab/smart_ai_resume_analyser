# AI Resume Analyzer — Complete Working Version

A Flask + MySQL/SQLite resume-analysis application implementing the complete workflow:

**Register/Login → PDF Upload → pdfplumber extraction → text preprocessing → profile/education/project/experience/skill extraction → target job → skill matching → TF-IDF + cosine similarity → ATS score → quality score → AI/local recommendations → results → analysis history.**

## Features

- User registration and login
- PDF drag-and-drop upload
- Two-column PDF extraction using pdfplumber
- Name, email, phone extraction
- Structured Education extraction (degree, institution, dates, CGPA/percentage)
- Experience extraction
- Project extraction
- Skill extraction with aliases
- Target job and experience-level selection
- Sample job-description templates
- Required / matched / missing skill analysis
- Skill Match percentage
- TF-IDF + cosine similarity percentage
- Transparent ATS score breakdown
- Resume Quality / completeness score
- Matched keyword list
- Recommendations
- Optional Gemini recommendation layer with local fallback
- MySQL or SQLite database
- Persistent analysis history
- Dashboard cards update immediately after analysis
- Latest analysis restored when the dashboard is reopened
- Non-destructive database migration for columns added by this version
- Render/Gunicorn configuration

## ATS scoring

The ATS score is a transparent project-specific weighted score:

- Skills: 40%
- Education: 15%
- Projects: 15%
- Experience: 15%
- Job-description keyword coverage: 15%

TF-IDF + cosine similarity is shown separately; it is not silently added to the ATS score.

## Setup — Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example`.

For MySQL:

```sql
CREATE DATABASE resume_ai;
```

Then set:

```env
SECRET_KEY=change-me
DATABASE_URL=mysql+pymysql://root:password@localhost/resume_ai
```

The application creates missing tables and adds the new optional columns to older project tables without deleting existing data.

For a quick SQLite test, omit `DATABASE_URL`.

Run:

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## Optional Gemini

The application works without Gemini. It uses the local recommendation engine by default.

If a Gemini API key is configured:

```env
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.0-flash
```

The app tries Gemini and automatically falls back to local recommendations if the API is unavailable or rate-limited.

## Main API endpoints

- `POST /resume/upload`
- `GET /resume/latest`
- `POST /analysis/analyze`
- `GET /analysis/latest`
- `GET /analysis/history`
- `GET /health`

## Test flow

1. Register a user.
2. Login.
3. Upload a text-based PDF resume.
4. Select a target role.
5. Select experience level.
6. Paste a JD or click **Use sample JD for selected role**.
7. Click **Analyze Resume**.
8. Confirm the dashboard updates ATS Score, Skill Match, Similarity, Resume Quality and the detailed results.
9. Refresh the dashboard; the latest analysis is restored from the database.

## Notes

- Scanned/image-only PDFs require OCR; this version intentionally uses pdfplumber as the project extraction engine.
- Never include `.env`, passwords, API keys, or a local `venv` in the project ZIP.
