import json
from app.config import COMPANIES_FILE

# ===================================== Question Bank =====================================
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

# ----------------------- Logic to combine questions for modes ----------------------
QUESTIONS_DB["balanced"] = QUESTIONS_DB["fast"] + QUESTIONS_DB["balanced"]
QUESTIONS_DB["detailed"] = QUESTIONS_DB["balanced"] + QUESTIONS_DB["detailed"]

# ----------------------- Function to load companies from file ----------------------
def load_companies():
    try:
        with open(COMPANIES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Companies file not found at {COMPANIES_FILE}")
        return []

companies_data = load_companies()
