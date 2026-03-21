import json
import time
from google import genai
from groq import Groq

from app.config import GEMINI_API_KEY, GROQ_API_KEY

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
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=prompt
            )
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
    return chat_completion.choices[0].message.content

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
def analyze_profile(user_context, candidates_json, mode, answers, resume_extracted, skip_providers=None):
    
    # Standard Prompt
    prompt = f"""
    Act as a senior career counselor and placement advisor. Analyze this student's profile against the matched companies.
    
    STUDENT PROFILE:
    {user_context}
    
    MATCHED COMPANIES (Use ALL companies from this list — do NOT invent new ones):
    {candidates_json}
    
    Generate a JSON object with:
    - candidate_name: String (Extract full name from resume, or return "Dear Student" if unknown)
    - readiness_score: Integer (0-100, be realistic — 60-80 for good students, 80+ only for exceptional)
    - strengths: List of 3 strings (Specific technical/soft strengths backed by their profile)
    - gaps: List of 3 strings (Concrete missing skills relevant to the matched roles)
    - action_plan: List of 3 actionable steps (Each should be specific: mention a course, platform, project idea, or certification)
    - job_recommendations: List of up to 5 objects from the MATCHED COMPANIES list above. Do NOT hallucinate companies.
      For each object include:
      - company: Company name (MUST exist in MATCHED COMPANIES above)
      - role: The role title
      - location: The location
      - match: A specific match reason explaining WHY this student fits (reference their actual skills/projects)
      - email_draft: A personalized cold email to this company's HR that:
        1. Opens with a specific hook (mention a company product/project or recent news if plausible)
        2. Highlights 2-3 of the student's relevant skills/projects by name
        3. Explains why they're excited about THIS specific role (not generic)
        4. Keeps it under 150 words, professional but not stiff
        5. Includes a clear call-to-action (request for interview/call)
    - email_draft: (Legacy field) A generic professional inquiry email template.
    
    Return ONLY valid JSON.
    """

    ai_data = None
    skip = skip_providers or set()
    
    # Provider Chain — Gemini first, Groq as fallback
    providers = [
        ("Gemini", call_gemini),
        ("Groq",   call_groq),
    ]
    
    for name, func in providers:
        if name in skip:
            print(f"Skipping {name} (failed during ranking)")
            continue
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
            "action_plan": ["Please check GEMINI_API_KEY and GROQ_API_KEY in .env"],
            "email_draft": "Error",
            "candidate_name": "Student",
            "job_recommendations": []
        }

    return ai_data

# ========================== Orchestration Logic =============================
from app.quiz import QUESTIONS_DB
from app.models import AIAnalysisResponse, sanitize_for_prompt
from app.services.resume_service import extract_resume_text_from_bytes
from app.services.matching_service import hard_filter_companies, quick_score_companies
from app.services.pdf_service import generate_pdf
from app.db_models import Company

def run_full_assessment(submission, db):
    """
    Hybrid Assessment Flow:
    1. Prepare Context (Answers + Resume)
    2. Load companies from PostgreSQL
    3. Hard Filter (Python — location, CTC, work mode)
    4. Quick Score (Python — regex skill/role matching) → Top 20
    5. LLM Intelligent Ranking → picks Top 5 from the 20
    6. LLM Full Analysis (strengths, gaps, action plan, emails)
    7. Generate PDF Report
    """

    # 1. User Data variables
    user_context = submission.get_formatted_context(QUESTIONS_DB)
    user_preferences = submission.get_user_preferences()

    # 2. Resume text extraction (from DB bytes, not filesystem)
    resume_text_full = ""
    resume_pdf_bytes = None
    if submission.resume_filename:
        if not submission.resume_filename.lower().endswith('.pdf'):
            print(f"Warning: Attempt to access non-pdf file {submission.resume_filename}")
        else:
            from app.db_models import ResumeUpload
            resume_record = db.query(ResumeUpload).filter(
                ResumeUpload.filename == submission.resume_filename
            ).order_by(ResumeUpload.uploaded_at.desc()).first()
            if resume_record and resume_record.pdf_binary:
                resume_pdf_bytes = resume_record.pdf_binary
                resume_text_full = resume_record.extracted_text or extract_resume_text_from_bytes(resume_pdf_bytes)
            else:
                print(f"Warning: Resume '{submission.resume_filename}' not found in database")

    profile_text = user_context
    if resume_text_full:
        profile_text += f"\n--- RESUME CONTENT ---\n{resume_text_full}"

    # 3. Load ALL companies from PostgreSQL
    all_companies = [c.to_dict() for c in db.query(Company).all()]
    print(f"Loaded {len(all_companies)} companies from database")

    # 4. Phase 1: Hard Filter (Python — fast, free, objective)
    filtered = hard_filter_companies(all_companies, user_preferences)

    # 5. Phase 2: Quick Score (Python — fast regex ranking) → Top 20
    top_20 = quick_score_companies(profile_text, filtered)

    # 6. Phase 3: LLM Intelligent Ranking — pick best 5 from 20
    sanitized_resume = sanitize_for_prompt(resume_text_full) if resume_text_full else ""
    user_context_for_llm = submission.get_formatted_context(QUESTIONS_DB)
    if sanitized_resume:
        user_context_for_llm += f"\n--- RESUME CONTENT ---\n{sanitized_resume}"

    candidates_for_ranking = json.dumps([{
        "id": c['id'], "name": c['name'], "role": c['role'],
        "location": c.get('location', ''), "skills": c['skills'],
        "score": c.get('score', 0)
    } for c in top_20])

    top_5, failed_providers = llm_rank_companies(user_context_for_llm, candidates_for_ranking)
    # Fallback: if LLM ranking fails, use the top 5 from quick_score
    if not top_5:
        top_5 = top_20[:5]

    # 7. Phase 4: LLM Full Analysis with the 5 best companies (skip providers that already failed)
    candidates_json = json.dumps([{
        "id": c['id'], "name": c['name'], "role": c['role'],
        "skills": c.get('skills', []), "email": c.get('email', '')
    } for c in top_5])

    ai_data = analyze_profile(user_context_for_llm, candidates_json, submission.mode, submission.answers, bool(resume_text_full), skip_providers=failed_providers)

    # 8. Validate AI response with Pydantic
    try:
        validated = AIAnalysisResponse(**ai_data)
        ai_data = validated.model_dump()
    except Exception as e:
        print(f"AI response validation warning: {e}")

    top_jobs = ai_data.get("job_recommendations", [])

    # 9. PDF Generation (in-memory, stored in DB)
    report_filename = f"Placement_Report_{int(time.time())}.pdf"
    final_data = {
        "mode": submission.mode,
        **ai_data,
        "job_recommendations": top_jobs
    }

    pdf_bytes = None
    try:
        pdf_bytes = generate_pdf(final_data, filename=report_filename)
    except Exception as e:
        print(f"PDF Gen Error: {e}")

    # pdf_url will be updated after DB commit (when we have the assessment ID)
    final_data["pdf_url"] = None

    # 10. Attach extra data for DB storage (not sent to frontend)
    final_data["_db_extra"] = {
        "resume_text": resume_text_full,
        "pdf_bytes": pdf_bytes,
        "pdf_filename": report_filename,
        "matched_companies": [
            {"name": c['name'], "role": c['role'], "location": c.get('location', ''), "score": c.get('score', 0)}
            for c in top_5
        ],
    }

    return final_data


# ========================== LLM Intelligent Ranking =============================
def llm_rank_companies(user_context, candidates_json):
    """
    Phase 3: Ask LLM to pick the best 5 companies from ~20 pre-filtered candidates.
    Returns (ranked_list or None, set_of_failed_provider_names).
    """
    prompt = f"""You are a placement advisor. Given the student profile and a list of pre-filtered companies,
select the TOP 5 best-matching companies for this student.

STUDENT PROFILE:
{user_context}

CANDIDATE COMPANIES (pre-filtered, with regex match scores):
{candidates_json}

Return ONLY a valid JSON array of the 5 best company IDs in order of best fit.
Example: [12, 5, 33, 7, 91]

Consider:
- How well the student's skills and interests align with the company's role
- Career growth potential for the student
- The regex score as a hint, but use your own judgment

Return ONLY the JSON array, nothing else.
"""

    providers = [
        ("Gemini", call_gemini),
        ("Groq", call_groq),
        ("Ollama", call_ollama)
    ]

    failed_providers = set()

    for name, func in providers:
        try:
            print(f"LLM Ranking — Attempting: {name}")
            raw = func(prompt)
            if not raw:
                failed_providers.add(name)
                continue
            cleaned = raw.strip().replace('```json', '').replace('```', '').strip()
            parsed = json.loads(cleaned)

            # Handle both plain array [1,2,3] and wrapped {"result": [1,2,3]}
            if isinstance(parsed, dict):
                ids = None
                for v in parsed.values():
                    if isinstance(v, list):
                        ids = v
                        break
                if not ids:
                    print(f"LLM Ranking — {name} returned dict with no list: {list(parsed.keys())}")
                    failed_providers.add(name)
                    continue
            elif isinstance(parsed, list):
                ids = parsed
            else:
                print(f"LLM Ranking — {name} returned unexpected type: {type(parsed)}")
                failed_providers.add(name)
                continue

            if len(ids) > 0:
                candidates = json.loads(candidates_json)
                id_to_company = {c['id']: c for c in candidates}
                ranked = [id_to_company[cid] for cid in ids if cid in id_to_company]
                if ranked:
                    print(f"LLM Ranking success ({name}): {[c['name'] for c in ranked]}")
                    return ranked[:5], failed_providers
                else:
                    print(f"LLM Ranking — {name} returned IDs that don't match candidates: {ids[:5]}")
                    failed_providers.add(name)
        except Exception as e:
            print(f"LLM Ranking — {name} failed: {e}")
            failed_providers.add(name)
            continue

    print("LLM Ranking failed — falling back to regex scores")
    return None, failed_providers
