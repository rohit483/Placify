import os
import pypdf

from app.config import RESUME_DIR

# ============================= Function to extract resume text =============================
def extract_resume_text(filename):
    path = os.path.join(RESUME_DIR, filename)
    text = ""
    try:
        if not os.path.exists(path): return ""
        if filename.endswith('.pdf'):
            reader = pypdf.PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Fallback for text/other files if supported later
            pass
    except Exception as e:
        print(f"Error reading resume: {e}")
    return text
