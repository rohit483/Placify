import requests
import json

def test_ollama_connection():
    url = "http://localhost:11434/api/generate"
    model = "gemma3:4b"

    print(f"Connecting to Ollama at {url} with model '{model}'...")

    payload = {
        "model": model,
        "prompt": "Say 'Hello from Ollama Local!'",
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("\n---------------- RESPONSE ----------------")
            print(data.get('response', 'No response field'))
            print("------------------------------------------")
            print("✅ Ollama Test Passed!")
        else:
            print(f"\n❌ Ollama Error: Status Code {response.status_code}")
            print(response.text)
            assert False, f"Ollama Error: {response.status_code}"

    except Exception as e:
        print(f"\n❌ Ollama Connection Failed: {e}")
        print("Ensure Ollama is running (`ollama serve`).")
        raise e

if __name__ == "__main__":
    test_ollama_connection()
