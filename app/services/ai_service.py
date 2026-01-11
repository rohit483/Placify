import json
import os
import time
from google import genai

from app.config import GEMINI_API_KEY, ANALYSIS_DIR

# ================================ LLM Model Setup =============================
client = None
model = None

if GEMINI_API_KEY: # Model Setup
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = 'gemini-2.5-flash'
else:
    print("Warning: Gemini API Key not loaded. AI features will not work.")

# ========================= Function to analyze user profile ========================= 
def analyze_profile(user_context, candidates_json, mode, answers, resume_extracted):
    if not client:
        # Mock Data if Key not loaded
        print("Using Mock Data (No API Key)")
        return {
            "readiness_score": 75,
            "strengths": ["Mock Strength 1", "Mock Strength 2"],
            "gaps": ["Mock Gap 1", "Mock Gap 2"],
            "action_plan": ["Mock Action 1", "Mock Action 2"],
            "email_draft": "Mock Email Draft",
            "candidate_name": "Mock Student",
            "job_recommendations": []
        }

# ---------------- Prompt to analyze profile ----------------
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
        The email must be professional, mention the specific role, and highlight the student's relevant strengths.
    
    - email_draft: (Legacy field, keep generic) "Generic inquiry..."
    
    Return ONLY valid JSON.
    """

# ---------------- to store response from Gemini ----------------
    try:
        print("Sending prompt to Gemini...")
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        print("Received response.")
        
        text_response = response.text.replace('```json', '').replace('```', '').strip()
        if text_response.startswith('json'):
            text_response = text_response[4:].strip()
        
        ai_data = json.loads(text_response) #gemini response
        
        # Creating analysis file
        timestamp = int(time.time())
        analysis_filename = f"analysis_{timestamp}.json"
        analysis_path = os.path.join(ANALYSIS_DIR, analysis_filename)
        
        # Saving analysis file
        with open(analysis_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "mode": mode,
                "submission": answers,
                "resume_extracted": resume_extracted,
                "candidates_provided": json.loads(candidates_json),
                "gemini_response": ai_data
            }, f, indent=4)
        print(f"Analysis saved to {analysis_path}")
        
        return ai_data #final response

# ---------------- Mock Data, if Gemini error even after key loaded ----------------
    except Exception as e:
        print(f"Gemini Error: {e}")
        # Return Error fallback structure
        return {
            "candidate_name": "Student",
            "readiness_score": 0,
            "strengths": [],
            "gaps": [],
            "action_plan": [],
            "email_draft": "Error generating report.",
            "job_recommendations": []
        }

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
    3. Analyze with AI (Gemini)
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
