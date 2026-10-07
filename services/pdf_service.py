import re
import pdfplumber


def _column_aware_page_text(page):
    """Extract a two-column resume in column order instead of PDF reading order."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False) or []
    if not words:
        return ""

    xs = sorted({round(float(w["x0"]), 1) for w in words})
    gaps = []
    for a, b in zip(xs, xs[1:]):
        gap = b - a
        if gap >= 20:
            left_count = sum(1 for w in words if float(w["x0"]) <= a)
            right_count = sum(1 for w in words if float(w["x0"]) >= b)
            if left_count >= 8 and right_count >= 8:
                gaps.append((gap, a, b))

    # A large internal x-gap usually means a two-column resume.
    if gaps:
        _, left_x, right_x = max(gaps, key=lambda item: item[0])
        split_x = (left_x + right_x) / 2
        left_words = [w for w in words if float(w["x0"]) < split_x]
        right_words = [w for w in words if float(w["x0"]) >= split_x]
        if len(left_words) >= 8 and len(right_words) >= 8:
            left = page.crop((0, 0, split_x, page.height)).extract_text() or ""
            right = page.crop((split_x, 0, page.width, page.height)).extract_text() or ""
            return f"{left.strip()}\n{right.strip()}".strip()

    return (page.extract_text(layout=False) or "").strip()


def extract_text_from_pdf(pdf_path):
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = _column_aware_page_text(page)
                if text:
                    pages.append(text)
        return "\n\n".join(pages).strip()
    except Exception as error:
        raise RuntimeError(f"Unable to extract PDF text: {error}")


def preprocess_text(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
