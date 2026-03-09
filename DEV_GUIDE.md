# Placify — Developer Guide

> Everything a developer needs to know before, during, and after working with this project.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Before You Start](#before-you-start)
4. [During Development](#during-development)
5. [Database Deep Dive](#database-deep-dive)
6. [API Reference](#api-reference)
7. [Security & Validation](#security--validation)
8. [Testing](#testing)
9. [Deployment (Production)](#deployment-production)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Clone and navigate
git clone https://github.com/rohit483/Placify.git
cd Placify

# 2. Create .env file (see "Environment Variables" section)
cp .env.example venv/.env
# Edit with your API keys

# 3. Start everything
docker compose up --build

# 4. Open browser
http://localhost
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER (Browser)                                │
│                         http://localhost                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          NGINX (Port 80)                                │
│         Reverse proxy + static file serving (/static/*)                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (Port 8000)                         │
│                                                                         │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐   │
│   │  routes/    │     │  services/  │     │      AI Providers       │   │
│   │  api.py     │───▶│  ai_service  │───▶│  Gemini → Groq → Ollama │   │
│   │  views.py   │     │  pdf_service│     │      (fallback chain)   │   │
│   └─────────────┘     │  resume_svc │     └─────────────────────────┘   │
│                       └──────┬──────┘                                   │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL (Port 5432)                               │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│   │   companies     │  │  resume_uploads │  │   assessments   │         │
│   │   (94 jobs)     │  │  (PDF + text)   │  │  (results+PDF)  │         │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Flows

| User Action | What Happens |
|-------------|--------------|
| Upload Resume | PDF → extract text → save to `resume_uploads` table |
| Take Assessment | Quiz answers + AI analysis → save to `assessments` table |
| Download PDF | Fetch binary from `assessments.pdf_binary` column |

---

## Before You Start

### Environment Variables

Create `venv/.env`:

```env
# Required — AI APIs
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# Required — Database
POSTGRES_USER=username_here
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=placify_db
DATABASE_URL=postgresql://username_here:your_secure_password@db:5432/placify_db

# Optional — Production
SKIP_SEED=false        # Set to "true" in production to disable auto-seeding
```

### Files You Should NEVER Commit

These should be in `.gitignore` (already configured):

```
venv/.env              # API keys and secrets
.env                   # Alternative location
__pycache__/           # Python bytecode
```

### Understanding the Codebase

| Directory/File | Purpose |
|----------------|---------|
| `main.py` | App entry point — initializes DB, seeds companies, mounts routes |
| `app/config.py` | All configuration, paths, environment loading |
| `app/database.py` | SQLAlchemy engine, session management, seeding logic |
| `app/db_models.py` | Table definitions (ORM models) |
| `app/models.py` | Pydantic models for validation |
| `app/quiz.py` | Question bank for assessments |
| `app/routes/api.py` | All API endpoints |
| `app/routes/views.py` | HTML page rendering |
| `app/services/ai_service.py` | AI orchestration (Gemini/Groq/Ollama) |
| `app/services/matching_service.py` | Job matching algorithms |
| `app/services/pdf_service.py` | PDF report generation |
| `app/services/resume_service.py` | PDF text extraction |
| `company_dataset/companies.json` | Seed data for companies table |

---

## During Development

### Docker Commands

```bash
# Start everything (with rebuild)
docker compose up --build

# Start in background
docker compose up --build -d

# Stop everything (keeps data)
docker compose down

# Stop and DELETE all database data (fresh start)
docker compose down -v

# View app logs
docker compose logs -f web

# View database logs
docker compose logs -f db

# Check container status
docker compose ps

# Restart just the backend (after code changes)
docker compose restart web
```

### Database Access

```bash
# Connect to PostgreSQL CLI
docker exec -it placify_db psql -U $POSTGRES_USER -d placify_db
```

Useful SQL queries:
```sql
-- Count records
SELECT COUNT(*) FROM companies;
SELECT COUNT(*) FROM assessments;
SELECT COUNT(*) FROM resume_uploads;

-- View recent assessments
SELECT id, candidate_name, readiness_score, mode, created_at 
FROM assessments ORDER BY created_at DESC LIMIT 10;

-- Search companies by skill
SELECT name, role FROM companies WHERE skills::text ILIKE '%python%';

-- Search resumes
SELECT filename FROM resume_uploads WHERE extracted_text ILIKE '%django%';

-- Exit psql
\q
```

### Making Code Changes

1. **Backend changes**: Docker auto-reloads (uvicorn `--reload` flag)
2. **Frontend changes**: Hard refresh browser (Ctrl+Shift+R) 
3. **Database model changes**: 
   ```bash
   docker compose down -v   # Delete volume
   docker compose up --build  # Recreate tables
   ```

### Cache Busting (CSS/JS)

When updating static files, bump the version in `template/index.html`:
```html
<link rel="stylesheet" href="/static/style.css?v=1.3">
<script src="/static/script.js?v=1.3"></script>
```

---

## Database Deep Dive

### Tables

#### `companies` — Job listings (seeded from JSON)

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Auto-incrementing PK |
| `name` | String(255) | Company name |
| `role` | String(255) | Job title |
| `location` | String(255) | City/region |
| `email` | String(255) | HR contact |
| `skills` | JSON | Required skills array |
| `description` | Text | Role description |
| `created_at` | DateTime | Record creation time |

#### `resume_uploads` — Uploaded resumes

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Auto-incrementing PK |
| `filename` | String | Original filename |
| `extracted_text` | Text | Full text from PDF |
| `pdf_binary` | BYTEA | Original PDF bytes |
| `client_ip` | String | Uploader's IP |
| `uploaded_at` | DateTime | Upload timestamp |

#### `assessments` — Assessment results

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Auto-incrementing PK |
| `mode` | String | fast/balanced/detailed |
| `candidate_name` | String | Name from resume |
| `resume_filename` | String | Associated resume |
| `readiness_score` | Float | 0-100 score |
| `answers` | JSON | Quiz responses |
| `ai_response` | JSON | Full AI analysis |
| `matched_companies` | JSON | Top 5 matches |
| `pdf_filename` | String | Report filename |
| `pdf_binary` | BYTEA | Generated PDF bytes |
| `client_ip` | String | User's IP |
| `created_at` | DateTime | Assessment time |

### Seeding Behavior

```python
# In app/database.py
def seed_companies_from_json():
    # 1. Check SKIP_SEED env var
    if os.getenv("SKIP_SEED") == "true":
        return  # Production: never seed
    
    # 2. Check if table has data
    if db.query(Company).count() > 0:
        return  # Already seeded, skip
    
    # 3. Load from JSON and insert
    # Only runs on first startup with empty table
```

**Key Point**: Editing `companies.json` does NOT update existing database records. It only seeds empty databases.

### How to Add New Companies

| Method | Command |
|--------|---------|
| Via API | `POST /api/dev/companies` with JSON body |
| Via SQL | `INSERT INTO companies (name, role, ...) VALUES (...)` |
| Fresh seed | `docker compose down -v` + restart |

---

## API Reference

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main page (HTML) |
| `GET` | `/quiz/questions` | Get quiz questions |
| `POST` | `/api/upload_resume` | Upload PDF resume |
| `POST` | `/api/assess` | Submit assessment |
| `GET` | `/api/report/pdf?assessment_id=1` | Download PDF report |

### Developer Endpoints (`/api/dev/`)

#### Assessments
```bash
GET  /api/dev/assessments           # List all
GET  /api/dev/assessments/1         # Full detail for #1
GET  /api/dev/assessments/1/pdf     # Download PDF
```

#### Resumes
```bash
GET  /api/dev/resumes               # List all
GET  /api/dev/resumes/1/text        # Get extracted text
GET  /api/dev/resumes/1/pdf         # Download original PDF
GET  /api/dev/resumes/search?q=python  # Search by keyword
```

#### Companies (CRUD)
```bash
GET    /api/dev/companies           # List all
GET    /api/dev/companies/search?q=backend  # Search
GET    /api/dev/companies/3         # Get by ID
POST   /api/dev/companies           # Create (JSON body)
PUT    /api/dev/companies/3         # Update (JSON body)
DELETE /api/dev/companies/3         # Delete
```

**Create/Update Company Body:**
```json
{
  "name": "Acme Corp",
  "role": "Backend Developer",
  "location": "Mumbai",
  "email": "hr@acme.com",
  "skills": ["Python", "Django", "PostgreSQL"],
  "description": "Building fintech APIs"
}
```

---

## Security & Validation

### 1. SQL Injection Protection

SQLAlchemy uses parameterized queries:
```python
# Safe (what we do):
record = Assessment(candidate_name=result.get("candidate_name"))
db.add(record)

# Dangerous (never do this):
db.execute(f"INSERT INTO assessments VALUES ('{name}')")
```

### 2. AI Response Validation (Pydantic)

```python
# app/models.py
class AIAnalysisResponse(BaseModel):
    readiness_score: float = 0      # Rejects non-numeric
    strengths: List[str] = []       # Ensures list of strings
    gaps: List[str] = []
    action_plan: List[str] = []
```

### 3. Prompt Sanitization

```python
# app/models.py
def sanitize_for_prompt(text: str) -> str:
    text = re.sub(r'[^\x20-\x7E\n\t\r]', '', text)  # Remove invisible chars
    return text[:5000]  # Cap length
```

### 4. Environment Security

| ✅ Safe | ❌ Dangerous |
|--------|-------------|
| API keys in `.env` | API keys in code |
| `.env` in `.gitignore` | Committing `.env` |
| `env_file:` in docker-compose | Hardcoded secrets |

---

## Testing

### Run Tests Locally

```bash
# Activate virtualenv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run with output
pytest -v
```

### CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs on every push:
1. **Python Quality**: flake8 linting
2. **Tests**: pytest
3. **Docker Build**: Verifies image builds

---

## Deployment (Production)

### Pre-Deployment Checklist

- [ ] Set strong `POSTGRES_PASSWORD` in `.env`
- [ ] Set `SKIP_SEED=true` (seed once manually, not every restart)
- [ ] Remove `--reload` from uvicorn command (see docker-compose.yml)
- [ ] Set proper `ALLOWED_HOSTS` if adding
- [ ] Use managed database (AWS RDS, Cloud SQL) instead of Docker PostgreSQL
- [ ] Use secret manager for API keys (AWS Secrets Manager, Azure Key Vault)

### Environment Variables for Production

```env
# Production .env
GEMINI_API_KEY=prod_key_here
GROQ_API_KEY=prod_key_here
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=very_long_secure_password_32chars
POSTGRES_DB=placify_prod
DATABASE_URL=postgresql://prod_user:password@managed-db-host:5432/placify_prod
SKIP_SEED=true
```

### Docker Compose for Production

Create `docker-compose.prod.yml`:
```yaml
services:
  web:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    # Remove --reload, add --workers
    env_file:
      - .env.prod
    # Don't mount volumes (use built image)
```

### Seeding in Production

```bash
# Option 1: Seed once manually
docker exec -it placify_backend python -c "
from app.database import seed_companies_from_json
from app.config import COMPANIES_FILE
seed_companies_from_json(str(COMPANIES_FILE))
"

# Option 2: Use admin API
POST /api/dev/companies  # Add companies one by one

# Option 3: Direct SQL import
docker exec -i placify_db psql -U user -d db < seed_data.sql
```

### Deployment Platforms

| Platform | Difficulty | Notes |
|----------|------------|-------|
| **Railway** | Easy | Docker support, managed Postgres |
| **Render** | Easy | Free tier, managed Postgres |
| **Fly.io** | Medium | Global edge deployment |
| **AWS ECS** | Hard | Full control, complex setup |
| **DigitalOcean** | Medium | App Platform or Droplets |

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `column "X" does not exist` | DB schema changed → `docker compose down -v` + rebuild |
| `GEMINI_API_KEY not found` | Check `.env` file exists and has correct key |
| `429 Resource Exhausted` | Gemini quota hit → waits and falls back to Groq |
| PDF download returns 404 | Check assessment was saved with `pdf_binary` |
| Companies not loading | Check `seed_companies_from_json` ran (see logs) |
| Changes not showing | Cache issue → Ctrl+Shift+R or bump `?v=` version |

### View Logs

```bash
# All services
docker compose logs

# Just backend (follow mode)
docker compose logs -f web

# Last 100 lines
docker compose logs --tail 100 web
```

### Reset Everything

```bash
# Nuclear option: delete all containers, volumes, rebuild
docker compose down -v
docker system prune -f
docker compose up --build
```

---

## Hybrid Matching Pipeline

How job matching works (for AI token efficiency):

```
User Profile
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: HARD FILTER (Python)                      FREE     │
│ Remove impossible matches (wrong city, low CTC, etc.)       │
│ 94 companies → ~40 remaining                                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: QUICK SCORE (Python regex)                FREE     │
│ Score by skill/role keyword overlap                         │
│ 40 companies → top 20                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: LLM RANKING (Gemini/Groq)           1 API CALL     │
│ Intelligent fit analysis: career growth, skill gaps         │
│ 20 companies → best 5                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: LLM ANALYSIS (Gemini/Groq)          1 API CALL     │
│ Full report: strengths, gaps, action plan, emails           │
│ Uses only 5 companies as context                            │
└─────────────────────────────────────────────────────────────┘
```

**Why?** LLMs are expensive. This pipeline keeps costs low by only sending 20 companies (not 94) to the AI.

---

## AI Provider Fallback

```
Request
   │
   ▼
┌──────────┐   429/Error   ┌──────────┐   Error   ┌──────────┐
│  GEMINI  │ ────────────▶│   GROQ    │────────▶ │  OLLAMA  │
│  (Free)  │               │  (Fast)  │           │ (Local)  │
└──────────┘               └──────────┘           └──────────┘
```

- **Gemini**: Primary, free tier, rate-limited
- **Groq**: Secondary, ultra-fast inference
- **Ollama**: Local fallback, no internet needed

If a provider fails during ranking, it's automatically skipped for the analysis phase too.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT QUICK REFERENCE                  │
├─────────────────────────────────────────────────────────────────┤
│ Start:        docker compose up --build                         │
│ Stop:         docker compose down                               │
│ Fresh DB:     docker compose down -v && docker compose up --build│
│ Logs:         docker compose logs -f web                        │
│ DB Shell:     docker exec -it placify_db psql -U $USER -d db    │
│ App URL:      http://localhost                                  │
│ API Debug:    http://localhost:8000/docs (Swagger)              │
├─────────────────────────────────────────────────────────────────┤
│                    ENVIRONMENT VARIABLES                        │
├─────────────────────────────────────────────────────────────────┤
│ GEMINI_API_KEY    Required   Primary AI                         │
│ GROQ_API_KEY      Required   Fallback AI                        │
│ DATABASE_URL      Required   PostgreSQL connection              │
│ SKIP_SEED         Optional   Set "true" in production           │
├─────────────────────────────────────────────────────────────────┤
│                    COMMON FIXES                                 │
├─────────────────────────────────────────────────────────────────┤
│ Schema error:     docker compose down -v                        │
│ No companies:     Check seed logs for errors                    │
│ 429 errors:       Normal, will fallback to Groq/Ollama          │
│ CSS not updating: Bump ?v= version in index.html                │
└─────────────────────────────────────────────────────────────────┘
```
