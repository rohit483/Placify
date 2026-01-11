import os
import json
import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse

from app.config import RESUME_DIR, PDF_DIR
from app.models import AssessmentSubmission
from app.quiz import QUESTIONS_DB
from app.services.ai_service import run_full_assessment

router = APIRouter(prefix="/api")

# ================================= Security: Rate Limiter =================================
class RateLimiter:
    def __init__(self, requests_per_minute=5):
        self.limit = requests_per_minute
        self.history = defaultdict(list)

    # Function to check rate limit
    def check(self, ip: str):
        now = time.time() 
        # Clean up old requests
        self.history[ip] = [t for t in self.history[ip] if now - t < 60] # Keep last 60 seconds
        
        if len(self.history[ip]) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        
        self.history[ip].append(now) # Add new request

limiter = RateLimiter(requests_per_minute=5)

# ================================= Backend APIs =================================
# ------------------- API that returns report(pdf) from server to client -------------------
# activate when client presses "download button"
@router.get("/report/pdf") 
async def get_report(filename: str):
    # Potential Path Traversal check (Simple)
    if ".." in filename or "/" in filename or "\\" in filename:
         return JSONResponse(status_code=400, content={"error": "Invalid filename"})

    file_path = os.path.join(PDF_DIR, filename)

    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": "File not found"})

# ------------------- API that uploads resume from client to server -------------------
# activate when client presses "upload resume" button
@router.post("/upload_resume") 
async def upload_resume(request: Request, file: UploadFile = File(...)):
    # 1. Rate Check
    client_ip = request.client.host
    limiter.check(client_ip)

    # 2. PDF Check
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are allowed"})
    
    if file.content_type != "application/pdf": 
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})

    try:
        file_location = os.path.join(RESUME_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return {"info": f"file '{file.filename}' saved at '{file_location}'", "filename": file.filename}

    except Exception as e:
        print(f"Server Error (Upload): {str(e)}") # Log internal error
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

# ------------------- API that returns(shows) questions from server to client -------------------
# activate when client presses "fast", "balanced" or "detailed" button
@router.get("/questions/{mode}") 
async def get_questions(mode: str):
    if mode not in QUESTIONS_DB:
        raise HTTPException(status_code=404, detail="Invalid mode")
    return QUESTIONS_DB[mode]

# ------------------- API that return answers and user's resume back to server -------------------
# activate when client presses "submit" button or "analyze resume" button
@router.post("/assess") 
async def generate_assessment(request: Request, submission: AssessmentSubmission):
    # 1. Rate Check
    client_ip = request.client.host
    limiter.check(client_ip)

    try:
        # 2. Delegate to AI Service (which handles the full orchestration)
        return run_full_assessment(submission)

    except Exception as e:
        print(f"Server Error (Assess): {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
