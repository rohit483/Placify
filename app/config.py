import os
from pathlib import Path
from dotenv import load_dotenv

# ======================================== PATHS ===================================
# --- Base Paths ---
# config.py is in app/, so parent is app, parent.parent is project root
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurable Paths ---
COMPANY_DATASET_DIR = BASE_DIR / "company_dataset"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "template"
#ENV_DIR = BASE_DIR / "venv"
ENV_DIR = BASE_DIR / "placify_env"

COMPANIES_FILE = COMPANY_DATASET_DIR / "companies.json"

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
DATABASE_URL = os.getenv("DATABASE_URL")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found under GEMINI_API_KEY.")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found. Fallback to Groq will not work.")
if not DATABASE_URL:
    print("Warning: DATABASE_URL not found. Database features will not work.")
