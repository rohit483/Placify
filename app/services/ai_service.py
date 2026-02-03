import json
import os
import time
import requests
from google import genai
from groq import Groq

from app.config import GEMINI_API_KEY, GROQ_API_KEY, ANALYSIS_DIR

# ================================ LLM Model Setup =============================
gemini_client = None
groq_client = None

# Initialize Gemini Client
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to init Gemini: {e}")

# Initialize Groq Client
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Failed to init Groq: {e}")

# ============================== Helper Functions =============================
# ----------------------- Function to call Gemini -----------------------
def call_gemini(prompt):
    if not gemini_client:
        raise Exception("Gemini Client not initialized")
    
    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    return response.text

# ----------------------- Function to call Groq -----------------------
def call_groq(prompt):
    if not groq_client:
        raise Exception("Groq Client not initialized")
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a JSON-only response bot. Output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    return chat_completion.choices[0].message.content

# Function to call Ollama
def call_ollama(prompt):
    url = "http://localhost:11434/api/generate" #add localhost llm url
    payload = {
        "model": "gemma3:4b",
        "prompt": prompt + "\nRespond with JSON only.",
        "stream": False,
        "format": "json" 
    }
    try:
        response = requests.post(url, json=payload, timeout=60) # 60s timeout for local
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            raise Exception(f"Ollama status: {response.status_code}")
    except Exception as e:
        raise Exception(f"Ollama connection failed: {e}")
# ============================== Response Cleaning =============================
# Function to clean JSON response
def clean_json_response(text_response):
    try:
        text_response = text_response.replace('```json', '').replace('```', '').strip()
        if text_response.startswith('json'):
            text_response = text_response[4:].strip()
        return json.loads(text_response)
    except:
        # Last cleanup attempt
        start = text_response.find('{')
        end = text_response.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text_response[start:end])
        raise

# ========================= Main Analysis Function ========================= 
def analyze_profile(user_context, candidates_json, mode, answers, resume_extracted):
    
    # Standard Prompt
    prompt = f"""
    Act as a career counselor. Analyze the following student profile and the provided list of matched companies.
    
    STUDENT PROFILE:
    {user_context}
    
    MATCHED COMPANIES (Select top 3 from this list ONLY):
    {candidates_json}
    
    Generate a JSON object with:
    - candidate_name: String (Extract full name from resume, or return "Dear Student" if unknown)
    - readiness_score: Integer (0-100)
    - strengths: List of 3 strings (Student's strengths)
    - gaps: List of 3 strings (Missing skills for these roles)
    - action_plan: List of 3 actionable steps
    - job_recommendations: List of 3 Objects from the "MATCHED COMPANIES" list provided above. Do NOT hallucinate companies.
      For each object include:
      - company: Name (Must exist in MATCHED COMPANIES)
      - role: Role
      - location: Location
      - match: Match Reason (Short string)
      - email_draft: A specific cold email draft to this company's HR.
    - email_draft: (Legacy field, keep generic) "Generic inquiry..."
    
    Return ONLY valid JSON.
    """

    ai_data = None
    
    # Provider Chain
    providers = [
        ("Gemini", call_gemini),
        ("Groq", call_groq),
        ("Ollama", call_ollama)
    ]
    
    for name, func in providers:
        try:
            print(f"Attempting Provider: {name}")
            raw_text = func(prompt)
            ai_data = clean_json_response(raw_text)
            if ai_data:
                print(f"Success with {name}")
                break
        except Exception as e:
            print(f"{name} Failed/Skipped: {e}")
            continue

    # Final Fallback (Mock) if all failed
    if not ai_data:
        print("All AI Providers failed. Using Mock Data.")
        return {
            "readiness_score": 0,
            "strengths": ["System Error"],
            "gaps": ["AI Service Unavailable"],
            "action_plan": ["Please check API keys or local Ollama"],
            "email_draft": "Error",
            "candidate_name": "Student",
            "job_recommendations": []
        }

    # Save Log
    try:
        timestamp = int(time.time())
        analysis_path = os.path.join(ANALYSIS_DIR, f"analysis_{timestamp}.json")
        with open(analysis_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "mode": mode,
                "provider_used": "unknown",
                "response": ai_data
            }, f, indent=4)
    except:
        pass
        
    return ai_data

# ========================== Orchestration Logic =============================
from app.quiz import QUESTIONS_DB, companies_data
from app.services.resume_service import extract_resume_text
from app.services.matching_service import rank_companies
from app.services.pdf_service import generate_pdf

def run_full_assessment(submission):
    """
    Orchestrates the full assessment flow:
    1. Prepare Context (Answers + Resume)
    2. Rank Companies (Hard Filter + Regex Score)
    3. Analyze with AI
    4. Generate PDF Report
    """

    # 1. User Data variables
    user_context_for_ranking = submission.get_formatted_context(QUESTIONS_DB)
    user_preferences = submission.get_user_preferences()

    # 2. Resume text extraction
    resume_text_full = ""
    if submission.resume_filename:
        if not submission.resume_filename.lower().endswith('.pdf'):
                print(f"Warning: Attempt to access non-pdf file {submission.resume_filename}")
        else:
            resume_text_full = extract_resume_text(submission.resume_filename)
            user_context_for_ranking += f"\n--- RESUME CONTENT ---\n{resume_text_full}"

    # 3. Company ranking variables
    top_candidates = rank_companies(user_context_for_ranking, companies_data, user_preferences)
    
    # 4. Quiz and resume prompt for Gemini
    user_context_for_gemini = submission.get_formatted_context(QUESTIONS_DB)
    if resume_text_full:
        user_context_for_gemini += f"\n--- RESUME CONTENT ---\n{resume_text_full[:4000]}..."
    
    # 5. Top 5 companies for Gemini
    candidates_json = json.dumps([{
        "id": c['id'], "name": c['name'], "role": c['role'], 
        "skills": c['skills'], "email": c['email']
    } for c in top_candidates])

    # 6. Top 3 companies by Gemini
    ai_data = analyze_profile(user_context_for_gemini, candidates_json, submission.mode, submission.answers, bool(resume_text_full))
    top_jobs = ai_data.get("job_recommendations", [])

    # 7. PDF Generation
    report_filename = f"Placement_Report_{int(time.time())}.pdf"
    final_data = {
        "mode": submission.mode,
        **ai_data,
        "job_recommendations": top_jobs
    }
    
    try:
        generate_pdf(final_data, filename=report_filename)
    except Exception as e:
        print(f"PDF Gen Error: {e}")

    final_data["pdf_url"] = f"/api/report/pdf?filename={report_filename}"
    
    return final_data
