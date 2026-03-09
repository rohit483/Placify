import io
import pypdf

# ============================= Function to extract resume text =============================
def extract_resume_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes (no filesystem needed)."""
    text = ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading resume: {e}")
    return text
