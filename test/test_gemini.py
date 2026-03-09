import os
import time
from google import genai
from dotenv import load_dotenv
from pathlib import Path

def test_gemini_connection():
    # Load env (Path Independent)
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_files = [BASE_DIR / ".env", BASE_DIR / "venv" / ".env", BASE_DIR / "placify_env" / ".env"]
    loaded = False
    for env_path in env_files:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            print(f"Loaded environment from {env_path}")
            loaded = True
            break

    if not loaded:
        print("Warning: No .env file found.")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY not found.")
        assert False, "GEMINI_API_KEY not found"

    print(f"✅ Found API Key: {GEMINI_API_KEY[:3]}...{GEMINI_API_KEY[-3:]}")

    try:
        print("Connecting to Gemini...")
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents="Say 'Hello from Gemini!'"
        )
        
        print("\n---------------- RESPONSE ----------------")
        print(response.text)
        print("------------------------------------------")
        print("✅ Gemini Test Passed!")

    except Exception as e:
        print(f"\n❌ Gemini Test Failed: {e}")
        raise e

if __name__ == "__main__":
    test_gemini_connection()
