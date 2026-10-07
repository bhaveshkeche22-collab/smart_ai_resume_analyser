import pdfplumber
import re


def extract_text_from_pdf(pdf_path):

    extracted_pages = []

    try:

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text:
                    extracted_pages.append(text)

        full_text = "\n".join(
            extracted_pages
        )

        return full_text.strip()

    except Exception as error:

        raise RuntimeError(
            f"Unable to extract PDF text: {error}"
        )


def preprocess_text(text):

    if not text:
        return ""

    # Convert multiple spaces to one
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    # Remove leading/trailing spaces
    text = text.strip()

    return text