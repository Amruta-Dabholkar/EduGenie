import re
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract


def clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()


def extract_with_pypdf2(filepath: str) -> str:
    """Primary extraction using PyPDF2."""
    text = []
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception as e:
        print(f"[PDF] PyPDF2 error: {e}")
    return "\n".join(text)


def extract_with_pdfminer(filepath: str) -> str:
    """Fallback extraction using pdfminer.six (handles complex layouts)."""
    try:
        return pdfminer_extract(filepath) or ""
    except Exception as e:
        print(f"[PDF] pdfminer error: {e}")
        return ""


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract text from a PDF file.
    Tries PyPDF2 first; falls back to pdfminer if result is too short.
    Returns cleaned text string, or empty string on failure.
    """
    text = extract_with_pypdf2(filepath)

    # If PyPDF2 gave too little text, try pdfminer
    if len(text.strip()) < 100:
        print("[PDF] PyPDF2 gave sparse output, trying pdfminer...")
        text = extract_with_pdfminer(filepath)

    if not text.strip():
        print("[PDF] Both extractors returned empty text.")
        return ""

    return clean_text(text)
