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
# ----------------------- Retry Configuration -----------------------
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 2  # seconds, will use exponential backoff

# ----------------------- Function to call Gemini with retry -----------------------
def call_gemini(prompt):
    if not gemini_client:
        raise Exception("Gemini Client not initialized")
    
    last_error = None
    for attempt in range(GEMINI_MAX_RETRIES):
        print(f"  [Gemini] Attempt {attempt + 1}/{GEMINI_MAX_RETRIES}...")
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            print("  [Gemini] ✓ Successfully generated response")
            return response.text
        except Exception as e:
            last_error = e
            error_str = str(e)
            
            # Check if it's a rate limit/overload error (503, 429)
            if '503' in error_str or '429' in error_str or 'UNAVAILABLE' in error_str or 'quota' in error_str.lower():
                wait_time = GEMINI_RETRY_DELAY * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                print(f"[Gemini] Rate limited, retry {attempt + 1}/{GEMINI_MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # Non-retryable error
                raise e
    
    # All retries exhausted
    raise last_error if last_error else Exception("Gemini failed after retries")

# ----------------------- Function to call Groq -----------------------
def call_groq(prompt):
    if not groq_client:
        raise Exception("Groq Client not initialized")
    
    # Enhanced system prompt for better email drafts
    system_prompt = """You are an expert career counselor and professional email writer. 
When generating email drafts, write COMPLETE, professional cold emails that include:
- A compelling subject line suggestion
- Proper greeting with company name
- 1-2 paragraphs: introduction, relevant skills/experience, call to action
- Professional closing with student's name
- Be specific about WHY the student is a good fit based on their profile

Output ONLY valid JSON. No markdown, no code blocks."""
    
    print("  [Groq] Attempting generation...")
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.7,  # Slightly more creative for better emails
        max_tokens=4000   # Allow longer responses for complete emails
    )
    print("  [Groq] ✓ Successfully generated response")
    return chat_completion.choices[0].message.content

# ------------------------ Function to call Ollama ------------------------
def call_ollama(prompt):
    url = "http://localhost:11434/api/generate" #add localhost llm url
    payload = {
        "model": "gemma3:4b",
        "prompt": prompt + "\nRespond with JSON only.",
        "stream": False,
        "format": "json" 
    }
    print("  [Ollama] Attempting generation...")
    try:
        response = requests.post(url, json=payload, timeout=60) # 60s timeout for local
        if response.status_code == 200:
            print("  [Ollama] ✓ Successfully generated response")
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
def analyze_profile(user_context, candidates_json, mode):
    
    # Enhanced Prompt with better email instructions
    prompt = f"""
    Act as a career counselor. Analyze the following student profile and the provided list of matched companies.
    
    STUDENT PROFILE:
    {user_context}
    
    MATCHED COMPANIES (Select top 5 from this list ONLY):
    {candidates_json}
    
    Generate a JSON object with:
    - candidate_name: String (Extract full name from resume, or return "Dear Student" if unknown)
    - readiness_score: Integer (0-100)
    - strengths: List of 3 strings (Student's strengths based on profile)
    - gaps: List of 3 strings (Missing skills for these roles)
    - action_plan: List of 3 actionable steps to improve placement readiness
    - job_recommendations: List of 5 Objects from the "MATCHED COMPANIES" list provided above. Do NOT hallucinate companies.
      For each object include:
      - company: Name (Must exist in MATCHED COMPANIES)
      - role: Role
      - location: Location  
      - match: Match Reason (Short string explaining fit)
      - email_draft: A COMPLETE professional cold email (150-200 words) including:
        * Subject line suggestion in first line
        * Greeting addressing company HR
        * Introduction paragraph (who you are, why contacting)
        * Skills/experience paragraph (specific skills matching the role)
        * Closing with call to action and professional sign-off
        * Use candidate's actual name if available
    
    IMPORTANT: Email drafts must be COMPLETE and PROFESSIONAL, not just 1-2 sentences.
    
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
            print(f"\n--- Analyzing profile with {name} ---")
            raw_text = func(prompt)
            print("  [System] Parsing LLM complete, parsing JSON array...")
            ai_data = clean_json_response(raw_text)
            if ai_data:
                print(f"  [{name}] ✓ Success in extracting recommendations.")
                recs = ai_data.get('job_recommendations', [])
                if recs:
                    print(f"  [{name}] Identified Top {len(recs)} matches:")
                    for i, rec in enumerate(recs):
                        print(f"     {i+1}. {rec.get('company', 'Unknown')} - {rec.get('role', 'Unknown')} (Draft generated: {bool(rec.get('email_draft'))})")
                else:
                    print(f"  [{name}] Warning: No recommendations returned in JSON array.")
                break
        except Exception as e:
            print(f"  [{name}] Failed/Skipped: {e}")
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
from app.services.pdf_service import generate_pdf

def run_full_assessment(submission):
    """
    Orchestrates the full assessment flow (Autonomous Agent Mode):
    1. Prepare Context (Answers + Resume)
    2. Dump entire Company JSON
    3. Analyze with AI
    4. Generate PDF Report
    """

    # 1. Prepare User Context
    user_context = submission.get_formatted_context(QUESTIONS_DB)
    
    resume_text_full = ""
    if submission.resume_filename:
        print(f"  [System] Loading resume file: {submission.resume_filename} ...")
        if not submission.resume_filename.lower().endswith('.pdf'):
                print(f"  [Warning] Attempt to access non-pdf file {submission.resume_filename}")
        else:
            resume_text_full = extract_resume_text(submission.resume_filename)
            print(f"  [System] ✓ Successfully parsed {len(resume_text_full)} characters from Resume.")
            # Add truncated resume to prevent massive token payloads if PDF is huge
            user_context += f"\n--- RESUME CONTENT ---\n{resume_text_full[:4000]}..."

    # 2. Dump all 94 companies for LLM reading
    print(f"  [System] Encoding comprehensive dataset of {len(companies_data)} companies into context payload...")
    candidates_json = json.dumps([{
        "name": c.get('name', ''), 
        "role": c.get('role', ''), 
        "skills": c.get('skills', []), 
        "email": c.get('email', ''),
        "description": c.get('description', ''),
        "ctc": c.get('ctc', 0),
        "location": c.get('location', '')
    } for c in companies_data])
    
    # 3. Analyze with AI (Removed unused parameters)
    ai_data = analyze_profile(user_context, candidates_json, submission.mode)
    top_jobs = ai_data.get("job_recommendations", [])

    # 4. PDF Generation
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
