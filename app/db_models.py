from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, LargeBinary
from sqlalchemy.sql import func
from app.database import Base

# ========================== Database Models for Companies ==========================
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    location = Column(String(255))
    email = Column(String(255))
    skills = Column(JSON)                      # List of skill strings
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "location": self.location or "",
            "email": self.email or "",
            "skills": self.skills or [],
            "description": self.description or "",
        }

# ========================== Database Models for Resume Uploads ==========================
class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    extracted_text = Column(Text)              # Full resume text for SQL search
    pdf_binary = Column(LargeBinary)           # Original PDF stored as bytes
    client_ip = Column(String(45))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

# ========================== Database Models for Assessments ==========================
class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String(50), nullable=False)
    candidate_name = Column(String(255))
    resume_filename = Column(String(255))
    readiness_score = Column(Float)
    answers = Column(JSON)
    ai_response = Column(JSON)
    matched_companies = Column(JSON)           # Top 5 companies with scores
    pdf_filename = Column(String(255))
    pdf_binary = Column(LargeBinary)           # Full PDF report stored in DB
    client_ip = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
