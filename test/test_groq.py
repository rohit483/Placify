import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

def test_groq_connection():
    # Load env from venv or local (Path independent)
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

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in environment.")
        # Fail pytest if key missing
        assert False, "GROQ_API_KEY not found in environment"

    print(f"✅ Found API Key: {api_key[:3]}...{api_key[-3:]}")

    try:
        print("Connecting to Groq...")
        client = Groq(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Say 'Hello from Groq!'"}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        print("\n---------------- RESPONSE ----------------")
        print(chat_completion.choices[0].message.content)
        print("------------------------------------------")
        print("✅ Groq Test Passed!")

    except Exception as e:
        print(f"\n❌ Groq Test Failed: {e}")
        raise e

if __name__ == "__main__":
    test_groq_connection()
