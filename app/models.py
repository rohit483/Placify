from pydantic import BaseModel
from typing import Dict, Any, Optional

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
