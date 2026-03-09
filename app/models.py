import re
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional, List

# ======================== Pydantic model to validate AI (LLM) response ========================
class JobRecommendation(BaseModel):
    company: str = "Unknown"
    role: str = "Unknown"
    location: str = "Remote/TBD"
    match: str = ""
    email_draft: str = ""

class AIAnalysisResponse(BaseModel):
    candidate_name: str = "Dear Student"
    readiness_score: float = 0
    strengths: List[str] = []
    gaps: List[str] = []
    action_plan: List[str] = []
    job_recommendations: List[JobRecommendation] = []
    email_draft: str = ""

    @field_validator("readiness_score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        """Safely convert LLM output to a number between 0-100."""
        try:
            score = float(v)
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, score))

    @field_validator("strengths", "gaps", "action_plan", mode="before")
    @classmethod
    def coerce_string_list(cls, v):
        """Ensure list fields are actually lists of strings."""
        if not isinstance(v, list):
            return [str(v)] if v else []
        return [str(item) for item in v]

# ======================== Prompt sanitization helper ========================
MAX_RESUME_CHARS = 5000  # Cap resume text sent to LLM

def sanitize_for_prompt(text: str) -> str:
    """Strip invisible/control characters and cap length before sending to LLM."""
    # Remove non-printable control chars (keep newlines, tabs, spaces)
    text = re.sub(r'[^\x20-\x7E\n\t\r]', '', text)
    return text[:MAX_RESUME_CHARS]

# ----------------- Function for data validation and formatting -----------------
class AssessmentSubmission(BaseModel):
    mode: str
    answers: Dict[str, Any]
    resume_filename: Optional[str] = None # Optional resume linkage

# ----------------------- Function to format Q&A context ----------------------
    def get_formatted_context(self, questions_db: Dict) -> str:
        """Constructs the Q&A context string."""
        questions_list = questions_db.get(self.mode, [])
        context = f"Assessment Mode: {self.mode}\n"
        for q in questions_list:
            key = f"q_{q['id']}"
            ans = self.answers.get(key, "Not Answered")
            context += f"Q: {q['text']}\nA: {ans}\n"
        return context

# ----------------------- Function to extract user preferences --------------------
    def get_user_preferences(self) -> Dict:
        """Extracts user preferences for ranking."""
        return {
            'location': self.answers.get('q_3', ''),
            'ctc_range': self.answers.get('q_4', ''),
            'work_environment': self.answers.get('q_26', '') 
        }
