import os
import json
import random
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import google.generativeai as genai
from fpdf import FPDF
import glob

# --- Configuration ---
API_KEY_FILE = "placify_env/gemini_api.txt"

def load_api_key():
    try:
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: API key file not found at {API_KEY_FILE}")
        return None

GEMINI_API_KEY = load_api_key()

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("Warning: Gemini API Key not loaded. AI features will not work.")
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
os.makedirs(RESUME_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)


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

# --- FastAPI Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

class AssessmentSubmission(BaseModel):
    mode: str
    answers: Dict[str, Any]
    resume_filename: str = None # Optional resume linkage

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
    else:
        # 1. Format User Context from Answers
        mode = submission.mode

    answers = submission.answers
    
    # Map Question IDs to their text for context
    questions_list = QUESTIONS_DB.get(mode, [])
    user_context = f"Assessment Mode: {mode}\n"
    
    # Creating a context string
    search_keywords = [] # For job matching
    
    for q in questions_list:
        key = f"q_{q['id']}"
        ans = answers.get(key, "Not Answered")
        user_context += f"Q: {q['text']}\nA: {ans}\n"
        
        # Collect keywords for simple RAG
        if q['id'] in [1, 2, 11, 14, 18]: # Tech related questions
             if ans != "Not Answered":
                 search_keywords.append(str(ans))

    prompt = f"""
    Act as a career counselor. Analyze the following student profile based on their assessment answers:
    
    {user_context}
    
    Generate a JSON object with:
    - readiness_score: Integer (0-100)
    - strengths: List of 3 strings
    - gaps: List of 3 strings
    - action_plan: List of 3 actionable steps
    - email_draft: A professional email to a recruiter text
    
    Return ONLY valid JSON.
    """

    try:
        if model:
            # 2. Call Gemini API
            response = model.generate_content(prompt)
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            ai_data = json.loads(text_response)

        # 3. Enhanced RAG Job Matching
        # Filter companies based on keywords found in answers
        recommended_jobs = []
        keyword_string = " ".join(search_keywords).lower()
        
        # If no specific tech keywords found (e.g. Fast mode might be sparse), use generic matching
        if not keyword_string and "Web Development" in user_context: keyword_string = "html css react"
        
        for company in companies_data:
            match_score = 0
            company_text = (company['description'] + " " + " ".join(company['skills'])).lower()
            
            # Simple term overlap
            company_skills = [s.lower() for s in company['skills']]
            for kw in keyword_string.split():
                # Allow partial matches e.g. "java" in "javascript" is a false positive risk, but good for prototype
                if kw in company_text: 
                    match_score += 10
            
            # Location preference check (simple)
            if "Indore" in user_context and company['location'] == "Indore":
                match_score += 20
                
            # Random jitter for variety if score is low
            if match_score == 0: match_score = random.randint(30, 60)
            else: match_score = min(99, 50 + match_score)

            job_entry = {
                "role": company['role'],
                "company": company['name'],
                "location": company['location'],
                "match": f"{match_score}%"
            }
            recommended_jobs.append(job_entry)

        # Sort by match score
        recommended_jobs.sort(key=lambda x: int(x['match'].strip('%')), reverse=True)
        top_jobs = recommended_jobs[:3]

        # 4. Generate PDF
        # Use timestamp to make filename unique
        import time
        report_filename = f"Placement_Report_{int(time.time())}.pdf"
        
        final_data = {
            "mode": mode,
            **ai_data,
            "job_recommendations": top_jobs
        }
        generate_pdf(final_data, filename=report_filename)
        
        # Add pdf_url to response
        final_data["pdf_url"] = f"/api/report/pdf?filename={report_filename}"

        return final_data

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
