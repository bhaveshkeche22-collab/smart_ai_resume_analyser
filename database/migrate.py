from sqlalchemy import inspect, text


def ensure_schema(db):
    """Create new tables and add non-destructive columns to older project databases."""
    db.create_all()
    inspector = inspect(db.engine)

    migrations = {
        "resumes": {
            "original_filename": "VARCHAR(255) NULL",
            "stored_filename": "VARCHAR(255) NULL",
            "file_path": "VARCHAR(500) NULL",
            "uploaded_at": "DATETIME NULL",
        },
        "extracted_data": {
            "certifications": "TEXT NULL",
            "achievements": "TEXT NULL",
            "summary": "TEXT NULL",
        },
        "analysis_results": {
            "education_score": "FLOAT NULL",
            "project_score": "FLOAT NULL",
            "experience_score": "FLOAT NULL",
            "keyword_score": "FLOAT NULL",
            "quality_score": "FLOAT NULL",
            "matched_skills": "TEXT NULL",
            "matched_keywords": "TEXT NULL",
        },
        "job_descriptions": {
            "created_at": "DATETIME NULL",
        },
    }

    for table, columns in migrations.items():
        existing = {c["name"] for c in inspector.get_columns(table)} if table in inspector.get_table_names() else set()
        for column, ddl in columns.items():
            if column not in existing:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
    db.session.commit()
