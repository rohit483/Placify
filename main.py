import os
import json
import random
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from google import genai
from fpdf import FPDF
import glob

# --- Configuration ---
API_KEY_FILE = "placify_env/gemini_api.txt"

def load_api_key():
    try:
        with open(API_KEY_FILE, "r") as f:
            content = f.read().strip()
            # Handle cases where the file contains "GEMINI_API_KEY = ..."
            if "=" in content:
                return content.split("=", 1)[1].strip()
            return content
    except FileNotFoundError:
        print(f"Error: API key file not found at {API_KEY_FILE}")
        return None

GEMINI_API_KEY = load_api_key()

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = 'gemini-2.5-flash'
else:
    print("Warning: Gemini API Key not loaded. AI features will not work.")
    client = None
    model = None

# --- Data Loading ---
COMPANIES_FILE = "company_dataset/companies.json"

def load_companies():
    try:
        with open(COMPANIES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Companies file not found at {COMPANIES_FILE}")
        return []

companies_data = load_companies()

# --- Storage Setup ---
RESUME_DIR = "web_data/resume"
PDF_DIR = "web_data/pdf"
ANALYSIS_DIR = "web_data/analysis"

os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)


# --- Question Bank ---
# Extracted from question_bank.txt
QUESTIONS_DB = {
    "fast": [
        {"id": 1, "text": "What is your primary area of interest?", "type": "mcq", "options": ["Web Development (Frontend/Backend/Fullstack)", "Data Science & AI/ML", "App Development (Android/iOS)", "Cybersecurity & Networks", "Non-Tech / Management"]},
        {"id": 2, "text": "Which programming language are you most comfortable with?", "type": "mcq", "options": ["Python", "Java", "C++", "JavaScript", "C#"]},
        {"id": 3, "text": "Preferred Work Location?", "type": "mcq", "options": ["Indore Only", "Bhopal Only", "Anywhere in Central India", "Remote / Work from Home"]},
        {"id": 4, "text": "What is your expected CTC (Annual Salary)?", "type": "mcq", "options": ["3-5 LPA", "5-8 LPA", "8-12 LPA", "12+ LPA"]},
        {"id": 5, "text": "How many internships have you completed?", "type": "mcq", "options": ["None", "1", "2", "3 or more"]},
        {"id": 6, "text": "Rate your communication skills (Self-Assessment).", "type": "mcq", "options": ["Basic", "Intermediate", "Advanced / Fluent", "Professional"]},
        {"id": 7, "text": "Are you open to working in startups?", "type": "mcq", "options": ["Yes, I prefer startups", "No, I prefer MNCs", "Open to both"]},
        {"id": 8, "text": "When are you available to join?", "type": "mcq", "options": ["Immediately", "In 1-2 months", "After graduation (6 months+)", "Only looking for Internships"]},
        {"id": 9, "text": "Do you have a portfolio or GitHub profile ready?", "type": "mcq", "options": ["Yes, extensive", "Yes, basic", "No, but working on it", "No"]},
        {"id": 10, "text": "Which of these best describes your current status?", "type": "mcq", "options": ["Final Year Student", "Fresh Graduate", "Looking for switch", "2nd/3rd Year Student"]}
    ],
    "balanced": [
        {"id": 11, "text": "List the top 3 technical skills/frameworks you have used in projects (e.g., React, Django, Pandas).", "type": "text"},
        {"id": 12, "text": "Describe your 'Best Project' in 1-2 sentences. What problem did it solve?", "type": "text"},
        {"id": 13, "text": "What is your preferred role type?", "type": "mcq", "options": ["Individual Contributor (Coding heavy)", "Team Lead / Management", "Research & Analysis", "Client Facing / Sales"]},
        {"id": 14, "text": "Have you done any certifications? If yes, list the most relevant one.", "type": "text"},
        {"id": 15, "text": "How would you rate your problem-solving skills (DSA)?", "type": "mcq", "options": ["Beginner", "Intermediate (LeetCode Easy/Medium)", "Advanced (Competitive Programmer)", "Not my focus"]},
        {"id": 16, "text": "Are you willing to learn a new tech stack for a job?", "type": "mcq", "options": ["Yes, absolutely", "Maybe, if it aligns with my goals", "No, I want to stick to my current stack"]},
        {"id": 17, "text": "What industry do you prefer?", "type": "mcq", "options": ["FinTech", "EdTech", "Healthcare", "E-commerce", "No Preference"]},
        {"id": 18, "text": "Do you have experience with Cloud platforms (AWS, Azure, GCP)?", "type": "mcq", "options": ["No", "Basic Knowledge", "Deployed projects", "Certified"]},
        {"id": 19, "text": "What is your biggest weakness you are working on?", "type": "text"},
        {"id": 20, "text": "Why do you think you are a good fit for the IT industry?", "type": "text"}
    ],
    "detailed": [
        {"id": 21, "text": "Describe a time you faced a technical challenge and how you solved it.", "type": "text"},
        {"id": 22, "text": "What are your career goals for the next 3 years?", "type": "text"},
        {"id": 23, "text": "Are you willing to relocate to a Tier-2 city (like Indore/Bhopal) permanently?", "type": "mcq", "options": ["Yes", "No", "Depends on the offer"]},
        {"id": 24, "text": "Mention any Hackathons or Coding Competitions you have participated in.", "type": "text"},
        {"id": 25, "text": "Do you have leadership experience (Clubs, Team Projects)?", "type": "text"},
        {"id": 26, "text": "What is your preferred work environment?", "type": "mcq", "options": ["Fast-paced & Chaotic", "Structured & Stable", "Remote & Flexible", "Collaborative Office"]},
        {"id": 27, "text": "Paste your LinkedIn URL (Optional).", "type": "text"},
        {"id": 28, "text": "If you have a gap in education, please explain briefly (write N/A if none).", "type": "text"},
        {"id": 29, "text": "What is one thing that makes you unique compared to other candidates?", "type": "text"},
        {"id": 30, "text": "Any specific companies in Indore/Bhopal you are targeting?", "type": "text"}
    ]
}
# Logic to combine questions for modes
QUESTIONS_DB["balanced"] = QUESTIONS_DB["fast"] + QUESTIONS_DB["balanced"]
QUESTIONS_DB["detailed"] = QUESTIONS_DB["balanced"] + QUESTIONS_DB["detailed"]

import pypdf

# Helper: Extract Text from Resume
def extract_resume_text(filename):
    path = os.path.join(RESUME_DIR, filename)
    text = ""
    try:
        if not os.path.exists(path): return ""
        if filename.endswith('.pdf'):
            reader = pypdf.PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Fallback for text/other files if supported later
            pass
    except Exception as e:
        print(f"Error reading resume: {e}")
    return text

# Helper: Rank Companies (Basic Logic)
def rank_companies(user_profile, companies):
    print(f"Ranking {len(companies)} companies...")
    scored_companies = []
    
    # Simple keyword scoring
    profile_lower = user_profile.lower()
    
    for company in companies:
        score = 0
        # Text to search in
        company_text = (company['name'] + " " + company['description'] + " " + " ".join(company['skills'])).lower()
        
        # Check for overlaps (Naive Approach for Prototype)
        
        # 1. Skill overlap
        for skill in company['skills']:
            if skill.lower() in profile_lower:
                score += 2
                
        # 2. Key role matching
        if company['role'].lower() in profile_lower:
            score += 5
            
        scored_companies.append((score, company))
        
    # Sort descending
    scored_companies.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 5
    return [c[1] for c in scored_companies[:5]]

# --- FastAPI Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

class AssessmentSubmission(BaseModel):
    mode: str
    answers: Dict[str, Any]
    resume_filename: Optional[str] = None # Optional resume linkage

# --- PDF Generation Report ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Placify - Personalized Career Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        # Ensure unicode characters don't crash FPDF (basic handling)
        body = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf(data, filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()

    # Introduction
    pdf.chapter_title(f"Assessment Mode: {data.get('mode', 'Unknown').capitalize()}")
    pdf.chapter_body(f"Candidate: {data.get('candidate_name', 'Student')}")
    pdf.chapter_body(f"Readiness Score: {data.get('readiness_score')}%")
    
    # Strengths
    pdf.chapter_title("Key Strengths")
    for s in data.get('strengths', []):
        pdf.chapter_body(f"- {s}")

    # Gaps
    pdf.chapter_title("Areas for Improvement")
    for g in data.get('gaps', []):
        pdf.chapter_body(f"- {g}")

    # Action Plan
    pdf.chapter_title("Action Plan")
    for i, p in enumerate(data.get('action_plan', [])):
        pdf.chapter_body(f"{i+1}. {p}")

    # Jobs
    pdf.chapter_title("Recommended Jobs")
    for job in data.get('job_recommendations', []):
        pdf.chapter_body(f"Role: {job['role']}\nCompany: {job['company']}\nLocation: {job['location']}\nMatch: {job['match']}")
        pdf.ln(2)

    output_path = os.path.join(PDF_DIR, filename)
    pdf.output(output_path)
    return output_path

# --- Routes ---
@app.get("/api/report/pdf")
async def get_report(filename: str):
    file_path = os.path.join(PDF_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.post("/api/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(RESUME_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return {"info": f"file '{file.filename}' saved at '{file_location}'", "filename": file.filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/script.js")
async def read_script():
    return FileResponse('script.js')

@app.get("/api/questions/{mode}")
async def get_questions(mode: str):
    if mode not in QUESTIONS_DB:
        raise HTTPException(status_code=404, detail="Invalid mode")
    return QUESTIONS_DB[mode]

@app.post("/api/assess")
async def generate_assessment(submission: AssessmentSubmission):
    """
    Analyzes assessment answers using Gemini and generates a report.
    """
    if not model:
        # Mock Data for functionality testing without API Key
        print("Using Mock Data (No API Key)")
        ai_data = {
            "readiness_score": 75,
            "strengths": ["Strong foundational knowledge", "Good approach to problem solving", "Clear communication style"],
            "gaps": ["Lack of practical project complexity", "Cloud deployment knowledge missing", "Unit testing experience"],
            "action_plan": ["Build a full-stack project with Auth", "Deploy app to AWS/Vercel", "Practice generic coding problems daily"],
            "email_draft": "Subject: Inquiry regarding Software Role\n\nDear Hiring Manager,\n\nI recently completed my assessment..."
        }
        
        # Proceed to job matching with mock data context
        user_context = f"Assessment Mode: {submission.mode}\n" # minimal context
        
        # Mock jobs for fallback
        top_jobs = [
            {"company": "Mock Co A", "role": "Dev", "location": "Indore", "match": "90%"},
            {"company": "Mock Co B", "role": "Tester", "location": "Remote", "match": "85%"},
            {"company": "Mock Co C", "role": "Analyst", "location": "Bhopal", "match": "80%"}
        ]
    else:
        # 1. Format User Context from Answers
        mode = submission.mode
        answers = submission.answers
        
        # Map Question IDs to their text for context
        questions_list = QUESTIONS_DB.get(mode, [])
        user_context = f"Assessment Mode: {mode}\n"
        
        search_keywords = [] 
        
        for q in questions_list:
            key = f"q_{q['id']}"
            ans = answers.get(key, "Not Answered")
            user_context += f"Q: {q['text']}\nA: {ans}\n"
            
            # Collect keywords for simple RAG
            if q['id'] in [1, 2, 11, 14, 18]: # Tech related questions
                 if ans != "Not Answered":
                     search_keywords.append(str(ans))

        # 1.5 Extract Resume Text if available
        resume_text = ""
        if submission.resume_filename:
            resume_text = extract_resume_text(submission.resume_filename)
            user_context += f"\n--- RESUME CONTENT ---\n{resume_text[:2000]}..." # Limit context size

        # 2. Pre-Filter Companies (RAG Lite)
        top_candidates = rank_companies(user_context, companies_data)
        candidates_json = json.dumps([{
            "id": c['id'], "name": c['name'], "role": c['role'], 
            "skills": c['skills'], "email": c['email']
        } for c in top_candidates])

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

        try:
            # 3. Call Gemini API (UPDATED for google-genai SDK)
            print("Sending prompt to Gemini...")
            
            # Use 'client.models.generate_content' instead of 'model.generate_content'
            response = client.models.generate_content(
                model=model,    # This passes the string 'gemini-1.5-flash'
                contents=prompt # This passes your prompt text
            )
            
            print("Received response.")
            
            # The new SDK still uses .text to get the string output
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            
            # Clean potential markdown issues
            if text_response.startswith('json'): 
                text_response = text_response[4:].strip()
            
            ai_data = json.loads(text_response)
            
            # Extract jobs from AI response
            top_jobs = ai_data.get("job_recommendations", [])
            
            # --- Persistence: Save Analysis ---
            import time
            timestamp = int(time.time())
            analysis_filename = f"analysis_{timestamp}.json"
            analysis_path = os.path.join(ANALYSIS_DIR, analysis_filename)
            
            with open(analysis_path, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "mode": mode,
                    "submission": answers,
                    "resume_extracted": bool(resume_text),
                    "candidates_provided": json.loads(candidates_json),
                    "gemini_response": ai_data
                }, f, indent=4)
            print(f"Analysis saved to {analysis_path}")
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            # Fallback if AI fails
            top_jobs = [] 
            ai_data = {"candidate_name": "Student", "readiness_score": 0, "strengths": [], "gaps": [], "action_plan": [], "email_draft": "Error generating report."}

    # 4. Generate PDF
    # Use timestamp to make filename unique
    import time
    report_filename = f"Placement_Report_{int(time.time())}.pdf"
        
    final_data = {
        "mode": submission.mode,
        **ai_data,
        "job_recommendations": top_jobs
    }
    try:
        generate_pdf(final_data, filename=report_filename)
    except Exception as e:
        print(f"PDF Error: {e}")

    # Add pdf_url to response
    final_data["pdf_url"] = f"/api/report/pdf?filename={report_filename}"

    return final_data



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
