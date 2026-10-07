import os
import re
import json

from flask import Flask
from config import Config
from database.models import db, DSAProblem


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DSA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "dsa_sheet.md"
)


def clean_text(value):
    if not value:
        return ""

    value = value.replace("\\&", "&")
    value = value.replace("**", "")
    value = value.replace("svg", "")

    return value.strip()


def extract_link(cell):
    if not cell:
        return None

    match = re.search(
        r"\[.*?\]\((.*?)\)",
        cell
    )

    if match:
        return match.group(1)

    return None


def generate_leetcode_search(title):
    """
    The uploaded sheet contains the Practice icon URL,
    not the actual LeetCode destination URL.

    Therefore we create a LeetCode search URL instead
    of guessing an exact problem URL.
    """

    from urllib.parse import quote

    query = quote(title)

    return (
        "https://leetcode.com/problemset/"
        "?search="
        + query
    )


def parse_day(line):
    match = re.search(
        r"\*\*Day\s+(\d+)\s*:\s*(.*?)\*\*",
        line
    )

    if match:
        return int(match.group(1)), clean_text(match.group(2))

    return None, None


def parse_problem_row(line, day_number, topic):
    if not line.startswith("|"):
        return None

    cells = [
        cell.strip()
        for cell in line.split("|")
    ]

    if len(cells) < 7:
        return None

    title = clean_text(cells[2])

    if not title:
        return None

    if title.lower() in [
        "problem",
        "------------------------",
        ":------------------------"
    ]:
        return None

    article_url = extract_link(
        cells[3] if len(cells) > 3 else ""
    )

    youtube_url = extract_link(
        cells[4] if len(cells) > 4 else ""
    )

    practice_url = extract_link(
        cells[5] if len(cells) > 5 else ""
    )

    difficulty = clean_text(
        cells[6] if len(cells) > 6 else ""
    )

    estimated_time = clean_text(
        cells[7] if len(cells) > 7 else ""
    )

    companies = []

    for cell in cells[9:]:
        matches = re.findall(
            r"\[([^\]]+)\]\(",
            cell
        )

        companies.extend(matches)

    return {
        "day_number": day_number,
        "topic": topic,
        "title": title,
        "difficulty": difficulty,
        "estimated_time": estimated_time,
        "article_url": article_url,
        "youtube_url": youtube_url,

        # Actual LeetCode search URL
        "practice_url": generate_leetcode_search(title),

        "companies": json.dumps(
            companies[:10]
        )
    }


def import_dsa():
    if not os.path.exists(DSA_FILE):
        print("DSA file not found:")
        print(DSA_FILE)
        return

    with open(
        DSA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        lines = file.readlines()

    current_day = None
    current_topic = None

    imported = 0

    for line in lines:

        day, topic = parse_day(line)

        if day:
            current_day = day
            current_topic = topic
            continue

        if current_day is None:
            continue

        problem = parse_problem_row(
            line,
            current_day,
            current_topic
        )

        if not problem:
            continue

        existing = DSAProblem.query.filter_by(
            day_number=problem["day_number"],
            title=problem["title"]
        ).first()

        if existing:
            continue

        item = DSAProblem(**problem)

        db.session.add(item)

        imported += 1

    db.session.commit()

    print(
        f"DSA import completed. "
        f"{imported} new problems added."
    )


if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        import_dsa()