import os
from pathlib import Path
from dotenv import load_dotenv

# ======================================== PATHS ===================================
# --- Base Paths ---
# config.py is in app/, so parent is app, parent.parent is project root
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurable Paths ---
COMPANY_DATASET_DIR = BASE_DIR / "company_dataset"
WEB_DATA_DIR = BASE_DIR / "web_data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "template"
#ENV_DIR = BASE_DIR / "placify_env"
ENV_DIR = BASE_DIR / "venv"

COMPANIES_FILE = COMPANY_DATASET_DIR / "companies.json"
RESUME_DIR = WEB_DATA_DIR / "resume"
PDF_DIR = WEB_DATA_DIR / "pdf"
ANALYSIS_DIR = WEB_DATA_DIR / "analysis"

# Ensure directories exist
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# =================================== API Keys Setup ====================================
ENV_FILES = [
    BASE_DIR / ".env",              # Standard location (Root)
    ENV_DIR / ".env"                # Custom location
]

loaded = False
for env_path in ENV_FILES:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment from {env_path}")
        loaded = True
        break

if not loaded:
    print(f"Warning: No .env file found. Checked: {[str(p) for p in ENV_FILES]}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found under GEMINI_API_KEY.")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found. Fallback to Groq will not work.")
