import json
import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models import AssessmentSubmission
from app.quiz import QUESTIONS_DB
from app.services.ai_service import run_full_assessment
from app.database import get_db
from app.db_models import ResumeUpload, Assessment, Company

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
async def get_report(assessment_id: int, db: Session = Depends(get_db)):
    """Download PDF report from database by assessment ID."""
    record = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not record or record.pdf_binary is None:
        return JSONResponse(status_code=404, content={"error": "PDF not found"})
    from fastapi.responses import Response
    return Response(
        content=record.pdf_binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={record.pdf_filename or 'report.pdf'}"}
    )

# ------------------- API that uploads resume from client to server -------------------
# activate when client presses "upload resume" button
@router.post("/upload_resume") 
async def upload_resume(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Rate Check
    client_ip = request.client.host if request.client else "unknown"
    limiter.check(client_ip)

    # 2. Filename & PDF Check
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No filename provided"})
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are allowed"})
    
    if file.content_type != "application/pdf": 
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})

    try:
        contents = file.file.read()

        # Extract text from PDF bytes (no filesystem needed)
        from app.services.resume_service import extract_resume_text_from_bytes
        extracted_text = extract_resume_text_from_bytes(contents)

        # Save to database only (PDF binary + extracted text)
        record = ResumeUpload(
            filename=file.filename,
            extracted_text=extracted_text,
            pdf_binary=contents,
            client_ip=client_ip,
        )
        db.add(record)
        db.commit()

        return {"info": f"file '{file.filename}' saved to database", "filename": file.filename}

    except Exception as e:
        db.rollback()
        print(f"Server Error (Upload): {str(e)}")
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
async def generate_assessment(request: Request, submission: AssessmentSubmission, db: Session = Depends(get_db)):
    # 1. Rate Check
    client_ip = request.client.host if request.client else "unknown"
    limiter.check(client_ip)

    try:
        # 2. Delegate to AI Service (which handles the full orchestration)
        result = run_full_assessment(submission, db)

        # 3. Extract DB-only data (not sent to frontend)
        db_extra = result.pop("_db_extra", {})

        # 4. Save assessment to database
        record = Assessment(
            mode=submission.mode,
            candidate_name=result.get("candidate_name"),
            resume_filename=submission.resume_filename,
            readiness_score=result.get("readiness_score"),
            answers=submission.answers,
            ai_response=result,
            matched_companies=db_extra.get("matched_companies"),
            pdf_filename=db_extra.get("pdf_filename"),
            pdf_binary=db_extra.get("pdf_bytes"),
            client_ip=client_ip,
        )
        db.add(record)
        db.commit()

        # Now we have the ID — set the PDF download URL
        result["pdf_url"] = f"/api/report/pdf?assessment_id={record.id}"

        return result

    except Exception as e:
        db.rollback()
        print(f"Server Error (Assess): {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

# ================================= Developer / Admin APIs =================================

# ------------------- List all assessments (metadata only) -------------------
@router.get("/dev/assessments")
async def list_assessments(db: Session = Depends(get_db)):
    rows = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "mode": r.mode,
            "candidate_name": r.candidate_name,
            "resume_filename": r.resume_filename,
            "readiness_score": r.readiness_score,
            "pdf_filename": r.pdf_filename,
            "client_ip": r.client_ip,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]

# ------------------- Get full assessment detail by ID -------------------
@router.get("/dev/assessments/{assessment_id}")
async def get_assessment_detail(assessment_id: int, db: Session = Depends(get_db)):
    record = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": record.id,
        "mode": record.mode,
        "candidate_name": record.candidate_name,
        "resume_filename": record.resume_filename,
        "readiness_score": record.readiness_score,
        "answers": record.answers,
        "ai_response": record.ai_response,
        "matched_companies": record.matched_companies,
        "pdf_filename": record.pdf_filename,
        "client_ip": record.client_ip,
        "created_at": str(record.created_at),
    }

# ------------------- Download PDF report from DB (no filesystem needed) -------------------
@router.get("/dev/assessments/{assessment_id}/pdf")
async def get_assessment_pdf(assessment_id: int, db: Session = Depends(get_db)):
    record = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not record or record.pdf_binary is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    from fastapi.responses import Response
    return Response(
        content=record.pdf_binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={record.pdf_filename or 'report.pdf'}"}
    )

# ------------------- List all uploaded resumes -------------------
@router.get("/dev/resumes")
async def list_resumes(db: Session = Depends(get_db)):
    rows = db.query(ResumeUpload).order_by(ResumeUpload.uploaded_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "has_text": bool(r.extracted_text),
            "has_pdf": bool(r.pdf_binary),
            "client_ip": r.client_ip,
            "uploaded_at": str(r.uploaded_at),
        }
        for r in rows
    ]

# ------------------- Read extracted resume text by ID -------------------
@router.get("/dev/resumes/{resume_id}/text")
async def get_resume_text(resume_id: int, db: Session = Depends(get_db)):
    record = db.query(ResumeUpload).filter(ResumeUpload.id == resume_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": record.id,
        "filename": record.filename,
        "extracted_text": record.extracted_text or "(no text extracted)",
    }

# ------------------- Download original resume PDF from DB -------------------
@router.get("/dev/resumes/{resume_id}/pdf")
async def get_resume_pdf(resume_id: int, db: Session = Depends(get_db)):
    record = db.query(ResumeUpload).filter(ResumeUpload.id == resume_id).first()
    if not record or record.pdf_binary is None:
        raise HTTPException(status_code=404, detail="Resume PDF not found")
    from fastapi.responses import Response
    return Response(
        content=record.pdf_binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={record.filename}"}
    )

# ------------------- Search resumes by keyword -------------------
@router.get("/dev/resumes/search")
async def search_resumes(q: str, db: Session = Depends(get_db)):
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    rows = db.query(ResumeUpload).filter(
        ResumeUpload.extracted_text.ilike(f"%{q}%")
    ).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "uploaded_at": str(r.uploaded_at),
        }
        for r in rows
    ]

# ================================= Company CRUD APIs =================================

# ------------------- List all companies -------------------
@router.get("/dev/companies")
async def list_companies(db: Session = Depends(get_db)):
    rows = db.query(Company).order_by(Company.id).all()
    return [r.to_dict() for r in rows]

# ------------------- Search companies by skill or name -------------------
@router.get("/dev/companies/search")
async def search_companies(q: str, db: Session = Depends(get_db)):
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    rows = db.query(Company).filter(
        (Company.name.ilike(f"%{q}%")) |
        (Company.role.ilike(f"%{q}%")) |
        (Company.description.ilike(f"%{q}%"))
    ).all()
    return [r.to_dict() for r in rows]

# ------------------- Get single company by ID -------------------
@router.get("/dev/companies/{company_id}")
async def get_company(company_id: int, db: Session = Depends(get_db)):
    record = db.query(Company).filter(Company.id == company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    return record.to_dict()

# ------------------- Create a new company -------------------
@router.post("/dev/companies")
async def create_company(data: dict, db: Session = Depends(get_db)):
    if not data.get("name") or not data.get("role"):
        raise HTTPException(status_code=400, detail="'name' and 'role' are required")
    record = Company(
        name=data["name"],
        role=data["role"],
        location=data.get("location", ""),
        email=data.get("email", ""),
        skills=data.get("skills", []),
        description=data.get("description", ""),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()

# ------------------- Update a company -------------------
@router.put("/dev/companies/{company_id}")
async def update_company(company_id: int, data: dict, db: Session = Depends(get_db)):
    record = db.query(Company).filter(Company.id == company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    if "name" in data:
        record.name = data["name"]
    if "role" in data:
        record.role = data["role"]
    if "location" in data:
        record.location = data["location"]
    if "email" in data:
        record.email = data["email"]
    if "skills" in data:
        record.skills = data["skills"]
    if "description" in data:
        record.description = data["description"]
    db.commit()
    db.refresh(record)
    return record.to_dict()

# ------------------- Delete a company -------------------
@router.delete("/dev/companies/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    record = db.query(Company).filter(Company.id == company_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(record)
    db.commit()
    return {"detail": f"Company '{record.name}' (ID {company_id}) deleted"}
