import os
from pathlib import Path
from dotenv import load_dotenv

# =================================== PATHS ===================================
# --- Base Paths ---
# config.py is in app/, so parent is app, parent.parent is project root
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurable Paths ---
COMPANY_DATASET_DIR = BASE_DIR / "company_dataset"
WEB_DATA_DIR = BASE_DIR / "web_data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "template"
ENV_DIR = BASE_DIR / "placify_env"

COMPANIES_FILE = COMPANY_DATASET_DIR / "companies.json"
RESUME_DIR = WEB_DATA_DIR / "resume"
PDF_DIR = WEB_DATA_DIR / "pdf"
ANALYSIS_DIR = WEB_DATA_DIR / "analysis"

# Ensure directories exist
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# =================================== API Keys Setup ====================================
API_KEY_FILE = ENV_DIR / "gemini_api.txt"

def load_api_key():
    try:
        if not API_KEY_FILE.exists():
             print(f"Error: API key file not found at {API_KEY_FILE}")
             return None
        with open(API_KEY_FILE, "r") as f:
            content = f.read().strip()
            # Handle cases where the file contains "GEMINI_API_KEY = ..."
            if "=" in content:
                return content.split("=", 1)[1].strip()
            return content
    except Exception as e:
        print(f"Error reading API key: {e}")
        return None

GEMINI_API_KEY = load_api_key()
