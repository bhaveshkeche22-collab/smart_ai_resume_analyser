"""
Learning Hub database seeder.

Run from the project root:
    python learning_seed.py

Before running:
1. Make sure app.py/config.py can initialize your Flask app.
2. Put your DSA markdown source at:
       data/dsa_sheet.md
   (copy the uploaded "Pasted markdown(2).md" file there.)

This script creates:
- Career roadmaps
- Study subjects + topics
- Internship opportunities
- DSA problems from the markdown sheet

It does NOT delete existing records.
"""

import re
from pathlib import Path
from datetime import datetime

from app import app
from database.models import (
    db,
    CareerRole,
    RoadmapStep,
    StudySubject,
    StudyTopic,
    DSAProblem,
    InternshipOpportunity,
)


# ============================================================
# CAREER ROADMAPS
# ============================================================

ROADMAPS = {
    "Data Scientist": {
        "description": "Roadmap from Python and statistics to machine learning, data visualization, projects and deployment.",
        "icon": "bi-bar-chart-line",
        "steps": [
            ("Python Fundamentals", "Build a strong Python foundation for data work.", "Python syntax, functions, OOP, exceptions, files, modules", "2–3 weeks"),
            ("NumPy & Pandas", "Learn numerical computing and practical data manipulation.", "NumPy arrays, Pandas DataFrame, cleaning, filtering, grouping", "2–3 weeks"),
            ("Statistics & Mathematics", "Understand the mathematical foundation behind data science.", "Mean, median, variance, probability, distributions, correlation", "2–3 weeks"),
            ("Data Visualization", "Turn data into clear and useful visual insights.", "Matplotlib, Seaborn, charts, dashboards, storytelling", "1–2 weeks"),
            ("SQL", "Learn to retrieve and analyze data from relational databases.", "SELECT, JOIN, GROUP BY, subqueries, aggregation", "2 weeks"),
            ("Machine Learning", "Build and evaluate predictive models.", "Regression, classification, decision trees, random forest, metrics", "4–6 weeks"),
            ("Advanced ML", "Improve model selection and production readiness.", "Feature engineering, tuning, cross-validation, pipelines", "3–4 weeks"),
            ("Projects", "Apply the complete data science workflow to real datasets.", "EDA, preprocessing, modeling, evaluation, reporting", "3–5 weeks"),
            ("Deployment", "Make models usable through applications and APIs.", "Flask/FastAPI, REST APIs, Git, deployment", "2–3 weeks"),
        ],
    },
    "AI / ML Engineer": {
        "description": "Roadmap for building machine learning and AI applications from fundamentals to deployment.",
        "icon": "bi-robot",
        "steps": [
            ("Python & Programming", "Master programming fundamentals.", "Python, OOP, data structures, Git", "2–3 weeks"),
            ("Math for ML", "Learn mathematical concepts used by ML models.", "Linear algebra, probability, statistics, calculus basics", "3–4 weeks"),
            ("Machine Learning", "Learn supervised and unsupervised learning.", "Regression, classification, clustering, model evaluation", "4–6 weeks"),
            ("Deep Learning", "Build neural-network based applications.", "ANN, CNN, RNN, optimization, PyTorch/TensorFlow", "4–6 weeks"),
            ("NLP", "Process and understand human language.", "Tokenization, embeddings, transformers, text classification", "3–4 weeks"),
            ("Generative AI", "Build applications using modern language models.", "LLMs, prompting, RAG, vector databases", "3–4 weeks"),
            ("MLOps & Deployment", "Deploy and maintain AI applications.", "APIs, Docker basics, monitoring, cloud deployment", "2–4 weeks"),
            ("AI Projects", "Build portfolio-ready end-to-end systems.", "RAG app, prediction system, chatbot, AI assistant", "4–6 weeks"),
        ],
    },
    "Software Developer": {
        "description": "Roadmap for becoming a software developer with strong programming, DSA, databases and project skills.",
        "icon": "bi-code-slash",
        "steps": [
            ("Programming Fundamentals", "Choose one main language and build strong fundamentals.", "Java/C++/Python, variables, loops, functions, OOP", "3–4 weeks"),
            ("DSA", "Develop problem-solving and coding interview skills.", "Arrays, strings, linked lists, stacks, queues, trees, graphs, DP", "8–12 weeks"),
            ("Databases", "Learn how applications store and query data.", "SQL, MySQL, normalization, joins, transactions", "2–3 weeks"),
            ("Web Development", "Build complete web applications.", "HTML, CSS, JavaScript, frontend/backend basics", "4–6 weeks"),
            ("Backend Development", "Create APIs and server-side applications.", "Flask/FastAPI/Node, REST APIs, authentication", "3–4 weeks"),
            ("Git & GitHub", "Manage and collaborate on software projects.", "Git, branches, pull requests, repositories", "1 week"),
            ("Projects", "Build applications that demonstrate your skills.", "CRUD app, API project, full-stack project", "4–6 weeks"),
            ("Interview Preparation", "Prepare for technical interviews.", "DSA practice, CS fundamentals, projects, resume", "4–8 weeks"),
        ],
    },
    "Data Analyst": {
        "description": "Roadmap for data analysis, SQL, visualization and business intelligence.",
        "icon": "bi-graph-up",
        "steps": [
            ("Excel", "Learn spreadsheet-based analysis.", "Formulas, lookup, pivot tables, charts", "1–2 weeks"),
            ("SQL", "Query and analyze relational data.", "SELECT, WHERE, JOIN, GROUP BY, subqueries", "2–3 weeks"),
            ("Python", "Automate analysis and work with datasets.", "Python, Pandas, NumPy", "2–3 weeks"),
            ("Statistics", "Understand analytical results.", "Descriptive statistics, probability, correlation", "2 weeks"),
            ("Visualization", "Create useful dashboards and reports.", "Power BI, Tableau, Matplotlib, dashboard design", "2–3 weeks"),
            ("Projects", "Build portfolio projects using real datasets.", "EDA, dashboards, business insights", "3–4 weeks"),
        ],
    },
    "Web Developer": {
        "description": "Roadmap for frontend and backend web application development.",
        "icon": "bi-globe2",
        "steps": [
            ("HTML & CSS", "Build structured and responsive web pages.", "HTML5, CSS3, Flexbox, Grid, responsive design", "2–3 weeks"),
            ("JavaScript", "Add interactivity and application logic.", "DOM, events, arrays, objects, async JavaScript", "3–4 weeks"),
            ("Frontend Framework", "Build modern frontend applications.", "React, components, state, routing, APIs", "3–5 weeks"),
            ("Backend", "Build server-side APIs.", "Flask/FastAPI/Node, REST, authentication", "3–5 weeks"),
            ("Database", "Persist application data.", "MySQL/PostgreSQL, SQL, relationships", "2–3 weeks"),
            ("Deployment", "Publish applications.", "GitHub, Render/cloud basics, environment variables", "1–2 weeks"),
            ("Projects", "Create portfolio-ready applications.", "Full-stack CRUD, authentication, API integration", "4–6 weeks"),
        ],
    },
}


# ============================================================
# STUDY MATERIAL
# ============================================================

STUDY = {
    "Programming": (
        "Core programming concepts needed for software and AI development.",
        "bi-code-square",
        [
            ("Variables & Data Types", "Understand variables, primitive data types and type conversion."),
            ("Control Flow", "Learn if/else, switch, loops and conditional logic."),
            ("Functions", "Create reusable functions and understand parameters and return values."),
            ("OOP", "Learn classes, objects, inheritance, polymorphism and encapsulation."),
            ("Exception Handling", "Handle runtime errors safely."),
            ("File Handling", "Read and write files using your programming language."),
        ],
    ),
    "Data Structures & Algorithms": (
        "Learn data structures and algorithms through concepts and problem solving.",
        "bi-diagram-3",
        [
            ("Arrays & Strings", "Traversal, searching, sorting, prefix sums and two pointers."),
            ("Linked Lists", "Singly and doubly linked lists, insertion, deletion and reversal."),
            ("Stacks & Queues", "LIFO/FIFO structures and their applications."),
            ("Trees & BST", "Binary trees, traversals, BST operations and problems."),
            ("Graphs", "BFS, DFS, shortest paths and graph applications."),
            ("Dynamic Programming", "State, recurrence, memoization and tabulation."),
            ("Greedy", "Greedy choice, scheduling and optimization problems."),
        ],
    ),
    "Database & SQL": (
        "Study relational databases and SQL for application development and analytics.",
        "bi-database",
        [
            ("SQL Basics", "SELECT, WHERE, ORDER BY, LIMIT and filtering."),
            ("Joins", "INNER, LEFT, RIGHT and multi-table joins."),
            ("Aggregation", "GROUP BY, HAVING, COUNT, SUM, AVG, MIN and MAX."),
            ("Subqueries", "Nested queries and correlated-query basics."),
            ("Normalization", "Reduce redundancy and improve database structure."),
            ("Transactions", "Understand COMMIT, ROLLBACK and transaction concepts."),
        ],
    ),
    "Machine Learning": (
        "Study the complete machine-learning workflow.",
        "bi-cpu",
        [
            ("ML Fundamentals", "Features, labels, training, testing and generalization."),
            ("Regression", "Linear and logistic regression concepts."),
            ("Classification", "Decision trees, random forest and classification metrics."),
            ("Clustering", "Unsupervised learning and clustering basics."),
            ("Model Evaluation", "Accuracy, precision, recall, F1, ROC-AUC and confusion matrix."),
            ("Feature Engineering", "Cleaning, encoding, scaling and useful feature creation."),
        ],
    ),
    "Web Development": (
        "Learn frontend, backend and deployment fundamentals.",
        "bi-globe",
        [
            ("HTML", "Semantic page structure and forms."),
            ("CSS", "Layout, Flexbox, Grid and responsive design."),
            ("JavaScript", "DOM, events, fetch and asynchronous programming."),
            ("Flask", "Routes, templates, forms, sessions and APIs."),
            ("REST APIs", "HTTP methods, JSON, status codes and API integration."),
            ("Deployment", "Environment variables, production server and hosting basics."),
        ],
    ),
    "AI & Generative AI": (
        "Learn modern AI application development.",
        "bi-stars",
        [
            ("NLP Basics", "Text preprocessing, tokenization and embeddings."),
            ("Transformers", "Understand the high-level transformer architecture."),
            ("LLMs", "Learn how language-model applications are built."),
            ("Prompt Engineering", "Create clear prompts and structured instructions."),
            ("RAG", "Retrieval, chunking, embeddings, vector search and generation."),
            ("Vector Databases", "Store and retrieve semantic embeddings."),
        ],
    ),
}


# ============================================================
# INTERNSHIPS
# ============================================================

INTERNSHIPS = [
    {
        "name": "AICTE Internship Opportunities",
        "organization": "AICTE",
        "opportunity_type": "Student Internship",
        "eligibility": "Eligibility varies by listed internship.",
        "period": "Varies",
        "description": "Check the official AICTE internship platform for current student opportunities and eligibility.",
        "official_url": "https://internship.aicte-india.org/",
    },
    {
        "name": "Internship Opportunities",
        "organization": "National Career Service",
        "opportunity_type": "Career / Internship",
        "eligibility": "Depends on the individual opportunity.",
        "period": "Varies",
        "description": "Use the official National Career Service platform to search current opportunities.",
        "official_url": "https://www.ncs.gov.in/",
    },
]


# ============================================================
# DSA MARKDOWN IMPORT
# ============================================================

def clean_markdown_value(value):
    """Convert a markdown table cell to plain text."""
    value = value.strip()
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"`(.*?)`", r"\1", value)
    value = value.replace("\\&", "&")
    return value.strip()


def extract_link(cell):
    """Return the URL from [label](url), or None."""
    m = re.search(r"\[[^\]]+\]\((.*?)\)", cell)
    return m.group(1).replace("\\&", "&").strip() if m else None


def is_header_or_separator(cells):
    joined = " ".join(cells).lower()
    if "problem" in joined and ("article" in joined or "practice" in joined):
        return True
    # Markdown separator row
    return all(re.fullmatch(r"\s*:?-+:?\s*", c or "") for c in cells)


def import_dsa(markdown_path):
    if not markdown_path.exists():
        print(f"[WARNING] DSA source not found: {markdown_path}")
        print("         Put your uploaded Pasted markdown(2).md here as data/dsa_sheet.md")
        return 0

    text = markdown_path.read_text(encoding="utf-8", errors="ignore")
    current_day = None
    current_topic = None
    imported = 0

    for raw in text.splitlines():
        line = raw.strip()

        # Examples:
        # **Day 2 : Array (Part 2)**
        # **Day 33 : Greedy**
        day_match = re.match(r"\*\*Day\s+(\d+)\s*:\s*(.*?)\*\*", line, re.I)
        if day_match:
            current_day = int(day_match.group(1))
            current_topic = clean_markdown_value(day_match.group(2))
            continue

        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or is_header_or_separator(cells):
            continue

        # Expected useful columns:
        # [blank, Problem, Article, Youtube, Practice, Level, Time, ...]
        # Some source rows have an extra first blank column.
        problem_index = 1 if len(cells) > 5 else 0

        title = clean_markdown_value(cells[problem_index])
        if not title or title.lower() in {"problem", "svg"}:
            continue

        # Ignore malformed SVG-only rows
        if title.lower() == "coming soon":
            continue

        article_index = problem_index + 1
        youtube_index = problem_index + 2
        practice_index = problem_index + 3
        difficulty_index = problem_index + 4
        time_index = problem_index + 5

        article_cell = cells[article_index] if article_index < len(cells) else ""
        youtube_cell = cells[youtube_index] if youtube_index < len(cells) else ""
        practice_cell = cells[practice_index] if practice_index < len(cells) else ""
        difficulty = clean_markdown_value(
            cells[difficulty_index] if difficulty_index < len(cells) else ""
        )
        estimated_time = clean_markdown_value(
            cells[time_index] if time_index < len(cells) else ""
        )

        article_url = extract_link(article_cell)
        youtube_url = extract_link(youtube_cell)
        practice_url = extract_link(practice_cell)

        # Skip rows that clearly aren't problems
        if title.lower() in {"youtube", "practice", "article"}:
            continue

        existing = DSAProblem.query.filter_by(
            day_number=current_day,
            title=title
        ).first()

        if existing:
            continue

        db.session.add(
            DSAProblem(
                day_number=current_day,
                topic=current_topic,
                title=title,
                difficulty=difficulty or None,
                estimated_time=estimated_time or None,
                article_url=article_url,
                youtube_url=youtube_url,
                practice_url=practice_url,
                companies=None,
            )
        )
        imported += 1

    return imported


# ============================================================
# SEED FUNCTIONS
# ============================================================

def seed_career_roadmaps():
    created = 0

    for role_name, data in ROADMAPS.items():
        role = CareerRole.query.filter_by(name=role_name).first()

        if not role:
            role = CareerRole(
                name=role_name,
                description=data["description"],
                icon=data["icon"],
            )
            db.session.add(role)
            db.session.flush()
            created += 1
        else:
            role.description = data["description"]
            role.icon = data["icon"]

        # Only add missing steps
        for number, (title, description, topics, estimated_time) in enumerate(data["steps"], 1):
            exists = RoadmapStep.query.filter_by(
                career_role_id=role.id,
                step_number=number,
            ).first()

            if not exists:
                db.session.add(
                    RoadmapStep(
                        career_role_id=role.id,
                        step_number=number,
                        title=title,
                        description=description,
                        topics=topics,
                        estimated_time=estimated_time,
                    )
                )

    return created


def seed_study_material():
    created = 0

    for name, (description, icon, topics) in STUDY.items():
        subject = StudySubject.query.filter_by(name=name).first()

        if not subject:
            subject = StudySubject(
                name=name,
                description=description,
                icon=icon,
            )
            db.session.add(subject)
            db.session.flush()
            created += 1
        else:
            subject.description = description
            subject.icon = icon

        for number, (title, topic_description) in enumerate(topics, 1):
            exists = StudyTopic.query.filter_by(
                subject_id=subject.id,
                order_number=number,
            ).first()

            if not exists:
                db.session.add(
                    StudyTopic(
                        subject_id=subject.id,
                        title=title,
                        description=topic_description,
                        order_number=number,
                    )
                )

    return created


def seed_internships():
    created = 0

    for item in INTERNSHIPS:
        exists = InternshipOpportunity.query.filter_by(
            name=item["name"],
            organization=item["organization"],
        ).first()

        if not exists:
            db.session.add(InternshipOpportunity(**item))
            created += 1

    return created


def main():
    with app.app_context():
        print("\n========================================")
        print("   LEARNING HUB DATABASE SEED")
        print("========================================\n")

        # Create tables that are represented by the SQLAlchemy models.
        db.create_all()

        careers = seed_career_roadmaps()
        study = seed_study_material()
        internships = seed_internships()

        dsa_file = Path("data") / "dsa_sheet.md"
        dsa = import_dsa(dsa_file)

        db.session.commit()

        print(f"Career roles created/updated : {careers}")
        print(f"Study subjects created       : {study}")
        print(f"Internships created          : {internships}")
        print(f"DSA problems imported        : {dsa}")

        print("\nCurrent database totals:")
        print(f"Career roles   : {CareerRole.query.count()}")
        print(f"Roadmap steps  : {RoadmapStep.query.count()}")
        print(f"Study subjects : {StudySubject.query.count()}")
        print(f"Study topics   : {StudyTopic.query.count()}")
        print(f"DSA problems   : {DSAProblem.query.count()}")
        print(f"Internships    : {InternshipOpportunity.query.count()}")

        print("\nDONE. Restart Flask and open Learning Hub.")


if __name__ == "__main__":
    main()
