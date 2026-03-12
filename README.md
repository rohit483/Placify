# Placify - AI-Driven Placement Readiness Platform

Placify is an intelligent career readiness platform designed to bridge the gap between students and their dream jobs. By leveraging Generative AI (Gemini, Groq, Ollama), Placify analyzes student profiles, resumes, and assessment responses to provide personalized career guidance, job recommendations, and actionable improvement plans.

## 🚀 Key Features

* **Multi-Mode Assessment**:
  * **Fast Mode**: Quick 10-question MCQ baseline check.
  * **Balanced Mode**: A mix of 20 MCQs and short answers for deeper insight.
  * **Detailed Mode**: Comprehensive analysis combining 30+ questions with resume parsing.
* **Resume Analysis (RAG-Powered)**: Upload your PDF resume to get a resume-only report or combine it with assessments for hyper-personalized results.
* **AI-Driven Insights**: Utilizes Google Gemini and Groq to generate:
  * Readiness Scores (0-100%).
  * Key Strengths & Improvement Gaps.
  * Tailored Action Plans.
  * Job Recommendations with personalized cold email drafts.
* **Hybrid Job Matching Pipeline**:
  * Phase 1: Hard filter (location, CTC, work mode)
  * Phase 2: TF-IDF + Cosine similarity (top 15 candidates)
  * Phase 3: LLM re-ranking (top 5 from 15)
  * Phase 4: Full AI analysis with matched companies
* **Professional Outputs**:
  * **PDF Reports**: Downloadable, well-formatted career reports stored in database.
  * **Email Drafting**: Auto-generated cold email drafts for recruiters.
* **Full-Stack Docker Deployment**: Nginx + FastAPI + PostgreSQL, production-ready.
* **Modern UI**: Clean, responsive interface with skeleton loading states.

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, Uvicorn, SQLAlchemy, scikit-learn |
| **Database** | PostgreSQL 15 (Docker) |
| **AI Engine** | Gemini 2.5-flash → Groq llama-3.3-70b → Ollama gemma3:4b |
| **Frontend** | HTML5, Vanilla CSS, JavaScript (ES6+) |
| **PDF Generation** | FPDF |
| **Reverse Proxy** | Nginx Alpine |
| **CI/CD** | GitHub Actions |

## 🛡️ AI Resilience System

Placify ensures zero downtime for AI features using a robust fallback mechanism:

```
Request → [Gemini] → 429/Error → [Groq] → Error → [Ollama (Local)]
```

Failed providers are automatically skipped in subsequent API calls within the same request.

## 📂 Project Structure

```bash
Placify/
├── .github/workflows/          # CI/CD (lint, test, docker build)
├── app/
│   ├── routes/                 # API endpoints (api.py, views.py)
│   ├── services/               # AI, PDF, resume, matching services
│   ├── config.py               # Configuration & environment loading
│   ├── database.py             # SQLAlchemy engine & seeding
│   ├── db_models.py            # ORM table definitions
│   ├── models.py               # Pydantic validation models
│   └── quiz.py                 # Question bank
├── static/                     # CSS & JavaScript
├── template/                   # HTML templates
├── test/                       # Test files (pytest)
├── company_dataset/
│   └── companies.json          # Seed data (94 job listings)
├── venv/
│   └── .env                    # API keys (not committed)
├── nginx/
│   └── nginx.conf              # Reverse proxy configuration
├── main.py                     # Application entry point
├── Dockerfile                  # Backend container
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Template for environment setup
├── .gitignore                  # Git ignore rules
├── .dockerignore               # Docker build exclusions
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview (this file)
├── DEV_GUIDE.md                # 📖 Complete developer documentation
└── LICENSE                     # MIT License
```

## ⚡ Getting Started

### Quick Start (Docker — Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/rohit483/Placify.git
cd Placify

# 2. Set up environment variables
cp .env.example venv/.env
# Edit venv/.env with your API keys

# 3. Start everything
docker compose up --build

# 4. Open browser
http://localhost
```

### Environment Variables

Create `venv/.env`:

```env
# Required
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
POSTGRES_USER=username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=placify_db
DATABASE_URL=postgresql://username:your_password@db:5432/placify_db

# Optional (for production)
SKIP_SEED=false
```

Get API keys:
* **Gemini**: [Google AI Studio](https://aistudio.google.com/)
* **Groq**: [Groq Console](https://console.groq.com/)

### Local Development (Without Docker)

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL locally and configure DATABASE_URL

# 4. Run
python main.py
```

### Optional: Ollama (Local AI Fallback)

```bash
# Install Ollama from https://ollama.com/
ollama pull gemma3:4b
ollama serve
```

## 📖 Usage

1. Open your browser and visit `http://localhost`.
2. **Select a Mode**: Choose Fast, Balanced, or Detailed assessment.
3. **Upload Resume**: Drag and drop your PDF resume for enhanced analysis.
4. **Submit**: Answer the questions and submit.
5. **View Report**: See your readiness score, strengths, and recommended jobs instantly.
6. **Download PDF**: Click "Download PDF Report" to save a copy.
7. **Draft Emails**: Select a recommended job to auto-generate a recruiter email.

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `placify_nginx` | 80 | Reverse proxy, serves static files |
| `placify_backend` | 8000 | FastAPI application |
| `placify_db` | 5432 | PostgreSQL database |

### Useful Commands

```bash
# Start
docker compose up --build

# Stop (keeps data)
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v

# View logs
docker compose logs -f web

# Access database
docker exec -it placify_db psql -U $POSTGRES_USER -d placify_db
```

## 📚 Developer Documentation

See **[DEV_GUIDE.md](DEV_GUIDE.md)** for complete documentation:

* Database schema and seeding
* API reference (all endpoints)
* Security & validation details
* Deployment checklist
* Troubleshooting guide

## 🔮 Future Scope

* **Advanced RAG**: Implement vector embeddings (ChromaDB/FAISS) for semantic resume-to-job matching.
* **Pan-India Expansion**: Expand the company dataset beyond Central India to all major tech hubs.
* **Admin Dashboard**: Web UI for managing companies without API calls.
* **User Accounts**: Authentication and assessment history tracking.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with ❤️ by Rohit*
