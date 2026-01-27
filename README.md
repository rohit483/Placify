# Placify - AI-Driven Placement Readiness Platform

Placify is an intelligent career readiness platform designed to bridge the gap between students and their dream jobs. By leveraging Generative AI (Google Gemini), Placify analyzes student profiles, resumes, and assessment responses to provide personalized career guidance, job recommendations, and actionable improvement plans.

## 🚀 Key Features

* **Multi-Mode Assessment**:
  * **Fast Mode**: Quick 10-question MCQ baseline check.
  * **Balanced Mode**: A mix of 20 MCQs and short answers for deeper insight.
  * **Detailed Mode**: Comprehensive analysis combining 30+ questions with resume parsing.
* **Resume Analysis (RAG-Powered)**: Upload your PDF resume to get an resume-Only report or combine it with assessments for hyper-personalized results.
* **AI-Driven Insights**: Utilizes Google Gemini to generate:
  * Readiness Scores (0-100%).
  * Key Strengths & Improvement Gaps.
  * Tailored Action Plans.
  * Job Recommendations (based on local/remote datasets).
* **Professional Outputs**:
  * **PDF Reports**: Downloadable, well-formatted career reports.
  * **Email Drafting**: Auto-generated cold email drafts for recruiters.
* **Performance & Security**:
  * Rate limiting API.
  * Input sanitization.
  * Secure environment variable management for API keys.
* **Modern UI**: Clean, responsive interface built with semantic HTML5 and optimized CSS (No external frameworks).

## 🛠️ Tech Stack

* **Backend**: Python, FastAPI, Uvicorn.
* **AI Engine**: Google Gemini API (`2.5-flash` model).
* **Frontend**: HTML5, Vanilla CSS (Modular), JavaScript (ES6+).
* **Data Handling**: JSON-based datasets, PyPDF (Resume parsing).
* **Reporting**: FPDF for dynamic PDF generation.

## 📂 Project Structure

```bash
Placify/
├── app/                        # Application Core
│   ├── routes/                 # API Endpoints (api.py, views.py)
│   ├── services/               # Logic Layer (ai_service, matching, pdf, resume)
│   ├── config.py               # Configuration & Path Management
│   ├── models.py               # Pydantic Data Models
│   └── quiz.py                 # Question Bank & Assessment Logic
├── static/                     # Static Assets
│   ├── style.css               # Main Stylesheet
│   └── script.js               # Frontend Logic
├── template/                   # HTML Templates
│   └── index.html              # Main Single-Page Interface
├── web_data/                   # Runtime Data Storage
│   ├── resume/                 # Uploaded Resumes (Temp)
│   ├── pdf/                    # Generated Reports
│   └── analysis/               # Raw JSON Analysis Logs
├── venv/                       # Environment Variables (Secure)
│   └── .env                    # API Keys (Not committed)
├── company_dataset/            # Data Sources
│   └── companies.json          # Job/Company Database
├── main.py                     # Entry Point
├── Dockerfile                  # Container Config
├── docker-compose.yml          # Container Orchestration
├── .dockerignore               # Docker Build Exclusions
└── requirements.txt            # Python Dependencies
```

## ⚡ Getting Started

### Prerequisites

* Python 3.9 or higher.
* A Google Gemini API Key (Get one [here](https://aistudio.google.com/)).

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/rohit483/Placify.git
   cd Placify
   ```
2. **Set up Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```
3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment**

   * Navigate to `venv/` folder.
   * Create a file named `.env`.
   * Add your API key:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     ```
5. **Run the Application**

   ```bash
   python main.py
   ```

   The server will start at `http://127.0.0.1:8000`.

## 📖 Usage

1. Open your browser and visit `http://127.0.0.1:8000`.
2. **Select a Mode**: Choose Fast, Balanced, or Detailed assessment.
3. **Upload Resume** (Optional): Drag and drop your PDF resume for enhanced analysis.
4. **Submit**: Answer the questions and submit.
5. **View Report**: See your readiness score, strengths, and recommended jobs instantly.
6. **Download PDF**: Click "Download PDF Report" to save a copy.
7. **Draft Emails**: Select a recommended job to auto-generate a recruiter email.

## 🐳 Docker Deployment

The application is fully containerized with Nginx and ready for database integration.

1. **Ensure Docker is installed**.
2. **Environment Setup**:
   Ensure your `.env` file exists at `venv/.env` (standard URL structure) or update `docker-compose.yml` to point to your custom location.
3. **Run with Docker Compose**:

   ```bash
   docker-compose up -d --build
   ```

   The app will be accessible at:
   *   **Frontend (Nginx)**: `http://localhost` (Recommended)
   *   **Backend Direct**: `http://localhost:8000`

## 🔮 Future Scope

* **Database Integration**: Migrate from file-based storage (JSON/PDF) to a robust SQL/NoSQL database for scalable data handling and faster RAG retrieval.
* **Pan-India Expansion**: Expand the company dataset to include opportunities across all major Indian tech hubs (Bangalore, Pune, Hyderabad, etc.), moving beyond the current Central India focus.
* **Advanced RAG**: Implement vector embeddings (ChromaDB/FAISS) for more accurate resume-to-job matching.

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
