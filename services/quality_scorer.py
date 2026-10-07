
def calculate_quality(information, text):
    checks = []
    score = 0
    rules = [
        ("name", bool(information.get("name")), 15, "Name detected"),
        ("email", bool(information.get("email")), 15, "Email detected"),
        ("phone", bool(information.get("phone")), 10, "Phone detected"),
        ("education", bool(information.get("education")), 15, "Education section detected"),
        ("skills", bool(information.get("skills")), 15, "Skills detected"),
        ("projects", bool(information.get("projects")), 10, "Projects detected"),
        ("experience", bool(information.get("experience")), 10, "Experience section detected"),
        ("summary", bool(information.get("summary")), 10, "Professional summary detected"),
    ]
    for key, ok, points, label in rules:
        if ok:
            score += points
            checks.append({"key": key, "status": True, "label": label})
        else:
            checks.append({"key": key, "status": False, "label": label})
    if len(str(text or "")) < 500:
        score = max(0, score - 5)
        checks.append({"key": "length", "status": False, "label": "Resume text is short"})
    else:
        checks.append({"key": "length", "status": True, "label": "Resume has sufficient text"})
    return round(float(score), 1), checks
