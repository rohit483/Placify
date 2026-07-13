# Technical Implementation Blueprint for Placify: A Retrieval-Augmented Placement Assistant

## 1. Executive Summary and Strategic Rationale

The transition from academic curricula to professional employment constitutes a critical friction point for engineering graduates, particularly in Tier-2 Indian cities where the disconnect between global generic advice and local hiring realities is most acute. The system, **'Placify,'** addresses this gap by architecting a unified, AI-powered placement assistant designed specifically for the Central India ecosystem.

This report delineates a comprehensive technical specification for Placify—a high-fidelity prototype that demonstrates the mechanics of AI-powered career guidance. The architecture prioritizes a "minimalist but sophisticated" approach, implementing intelligent matching through a **Hybrid Algorithm** that combines rule-based filtering with Large Language Model (LLM) reasoning.

**Implementation Status: ✅ FULLY OPERATIONAL**

The core objective is to operationalize a stateless, privacy-first web application that integrates assessment modes, resume parsing, and generative AI analysis. Unlike commercial SaaS platforms that rely on opaque cloud services, Placify's prototype is engineered to run entirely on a development machine (localhost), using a Python FastAPI backend to orchestrate logic and a vanilla HTML/JS frontend for user interaction.

By targeting a curated dataset of **94+ companies** within the Indore-Bhopal IT corridor, Placify moves beyond the hallucinations common in generic Large Language Models (LLMs). It grounds its recommendations in verifiable local market intelligence, ensuring that students receive actionable advice—such as specific contact emails and role-relevant skill gaps—rather than abstract career guidance.

---

## 2. Architectural Philosophy: The Stateless Minimalist Prototype

### 2.1 The Case for a "No-Login" Architecture

The system implements a "Stateless Service Model" with file-based persistence. In traditional web development, user authentication (AuthN) and persistent sessions significantly increase code complexity, requiring database management for credentials, session token handling (JWT/OAuth), and security compliance for personal data storage.

For Placify, the removal of the login requirement enables a **Privacy-First design pattern**. The system operates as a transient processor with local storage: data flows from the client (student) to the server, is processed to generate a report, and is stored locally for retrieval without requiring user accounts.

| Feature | Traditional Web App | Placify Prototype | Benefit for Prototype |
| :--- | :--- | :--- | :--- |
| **Authentication** | OAuth2 / JWT / Database | None (Open Access) | Zero setup time; eliminates barrier to entry for testing. |
| **Data Persistence** | PostgreSQL / MongoDB | File-based (JSON/PDF) | Simplifies deployment; no database setup required. |
| **Session State** | Server-side Redis / Cookies | Client-side + Local Files | Reduces backend logic; portable storage. |
| **Infrastructure** | Docker / Cloud Clusters | Local Python Process | Runs on any standard development laptop (8GB RAM). |

### 2.2 Technology Stack Selection

The selection of the technology stack is driven by the dual needs of "minimalism" (ease of setup) and "capability" (supporting advanced AI operations).

**Frontend: Vanilla HTML5, CSS3, and JavaScript (ES6+)**
A build-free Vanilla JS approach eliminates the need for Node.js package managers (npm/yarn), transpilers (Babel), and bundlers (Webpack). The frontend utilizes a professional LinkedIn-inspired design with custom system fonts and privacy-first consent checks, all contained in simple HTML/CSS/JS files, allowing for instant "save-and-refresh" debugging.

**Backend: Python 3.11+ with FastAPI**
Python is the non-negotiable language of choice due to its dominance in the AI/ML ecosystem. FastAPI is selected over Flask or Django for three specific reasons:
1. **Asynchronous Concurrency:** AI pipelines involve I/O bound operations (reading files, calling AI APIs). FastAPI's async/await syntax handles these efficiently.
2. **Data Validation:** Pydantic models strictly validate incoming data, preventing runtime errors from malformed inputs.
3. **Documentation:** Automatic interactive API documentation (Swagger UI) for testing endpoints.

**AI Layer: Triple-Provider Fallback System**
To ensure 99.9% availability, the system implements a cascading fallback chain:

| Priority | Provider | Model | Use Case |
|----------|----------|-------|----------|
| Primary | Google Gemini | gemini-2.5-flash | Production (fast, high-quality) |
| Secondary | Groq | llama-3.3-70b-versatile | Fallback (excellent reasoning) |
| Tertiary | Ollama | gemma3:4b | Local fallback (always available) |

---

## 3. The Intelligent Backend: Theoretical Foundations

### 3.1 Mathematical Foundations of Semantic Matching

The intelligent backend of Placify is grounded in the principles of **Vector Space Models** and **Information Retrieval**. While the implemented system uses a hybrid approach, understanding the theoretical foundations is essential.

**The Vector Space Model:**
Any piece of text (a student's resume or a company's job description) can be represented as a vector—a fixed-length list of numbers—in a high-dimensional space. The geometric distance between two vectors corresponds to their semantic similarity.

**The Transformation:**
$$f(\text{text}) \rightarrow \vec{v} \in \mathbb{R}^n$$
Where $n$ is the dimension of the embedding space.

**The Metric: Cosine Similarity**
To find the "Best Fit" company for a student, one calculates the angle between the Student Vector ($\mathbf{A}$) and every Company Vector ($\mathbf{B}$). The Cosine Similarity is defined as:

$$ \text{Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{|\mathbf{A}| |\mathbf{B}|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}} $$

If the vectors point in the exact same direction (perfect match), the angle is 0, and the cosine is 1. If they are orthogonal (unrelated), the cosine is 0.

### 3.2 Implemented Approach: Hybrid Matching Algorithm

While pure vector embedding approaches are theoretically elegant, the implemented system uses a **Hybrid Matching Algorithm** that offers several practical advantages:

**Why Hybrid TF-IDF + LLM:**
- **Mathematical Rigor:** TF-IDF provides industry-standard text similarity scoring
- **Controllability:** Hard filters eliminate clearly unsuitable matches before scoring
- **Scalability:** Efficient sparse matrix operations via scikit-learn
- **Semantic Depth:** LLM re-ranking captures nuances TF-IDF cannot

**The Three-Stage Pipeline:**

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  Stage 1:      │────▶│  Stage 2:      │────▶│  Stage 3:      │
│  Hard Filters  │     │  TF-IDF        │     │  LLM-Powered   │
│  (Elimination) │     │  Cosine Sim    │     │  Re-ranking    │
│  94 → ~80      │     │  ~80 → 15      │     │  15 → 5        │
└────────────────┘     └────────────────┘     └────────────────┘
```

**Stage 1: Hard Filter Function**
$$F_{\text{hard}}(s, c) = \begin{cases} 1 & \text{if } \text{loc}_c \in \text{pref}_s \land \text{ctc}_c \in \text{range}_s \land \text{mode}_c \in \text{pref}_s \\ 0 & \text{otherwise} \end{cases}$$

Where:
- $\text{loc}_c$ = company location (Indore, Bhopal, Remote)
- $\text{pref}_s$ = student's location preferences
- $\text{ctc}_c$ = company CTC offering
- $\text{range}_s$ = student's expected CTC range
- $\text{mode}_c$ = work mode (Remote, Hybrid, On-site)

**Stage 2: TF-IDF Vectorization + Cosine Similarity**

The system uses scikit-learn's `TfidfVectorizer` to transform text into weighted term vectors:

$$\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$$

Where:
- $\text{TF}(t, d)$ = Term frequency of term $t$ in document $d$
- $\text{IDF}(t) = \log\left(\frac{N}{df(t)}\right)$ where $df(t)$ = documents containing term $t$

**Cosine Similarity** measures the angle between student profile vector $\mathbf{S}$ and company vector $\mathbf{C}$:

$$\text{sim}(\mathbf{S}, \mathbf{C}) = \frac{\mathbf{S} \cdot \mathbf{C}}{|\mathbf{S}| \times |\mathbf{C}|} = \frac{\sum_{i=1}^{n} S_i C_i}{\sqrt{\sum_{i=1}^{n} S_i^2} \times \sqrt{\sum_{i=1}^{n} C_i^2}}$$

**Implementation:** Using unigrams + bigrams with 5000 max features:
```python
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words='english',
    ngram_range=(1, 2),
    max_features=5000
)
```

**Stage 3: LLM Re-ranking**
The top-15 TF-IDF candidates are passed to the LLM for semantic re-ranking considering:
- Career trajectory alignment
- Cultural fit indicators
- Growth potential
- Hidden relevance patterns beyond keyword matching

---

## 4. Data Engineering: The Central India Knowledge Base

The efficacy of any intelligent matching system is bounded by the quality of its underlying data. A generic LLM knows about Google and Microsoft; it likely does not know about specific mid-sized firms in the Crystal IT Park, Indore.

### 4.1 Data Sourcing Strategy

The dataset targets the Indore-Bhopal-Jabalpur IT corridor with **94+ verified companies**.

**Target Ecosystems:**
- **Indore:** Crystal IT Park, Super Corridor, Electronic Complex
- **Bhopal:** IT Park Badwai, MP Nagar Business District
- **Jabalpur:** IT Park Bargi Hills, Emerging Tech Clusters

**Data Acquisition Channels:**
1. **Institutional Placement Records:** Placement Cell Archives containing verified recruiters
2. **Regional NASSCOM & Industry Directories:** High-trust member lists
3. **Geo-Targeted Professional Search:** LinkedIn filters for company discovery
4. **Company "Careers" Pages:** Direct verification of technology stacks

### 4.2 Data Schema and Formatting

```json
{
  "name": "Company Name",
  "location": "Indore",
  "tech_stack": ["Python", "Django", "React", "AWS"],
  "roles": ["Software Developer", "Full Stack Engineer"],
  "description": "Detailed company description...",
  "contact": {
    "email": "careers@company.com",
    "linkedin": "https://linkedin.com/company/..."
  },
  "hiring_status": "active",
  "min_experience": 0,
  "preferred_experience": "0-3 years",
  "company_size": "medium",
  "verification_date": "2024-01-15"
}
```

**Schema Rationale:**
- **Matching Fields:** `tech_stack`, `roles`, `description` are used for scoring
- **Generation Fields:** `contact`, `verification_date` are passed to LLM for report generation
- This separation of "Searchable Data" and "Payload Data" prevents hallucination

---

## 5. Resume Intelligence Implementation

### 5.1 PDF Parsing Pipeline

The "Resume Intelligence" module is built using the `PyPDF2` library for text extraction.

**Implementation Logic:**
```python
from PyPDF2 import PdfReader

def extract_resume_text(file_path: str) -> str:
    """
    Extract and sanitize text from PDF resume.
    
    Args:
        file_path: Path to uploaded PDF file
    
    Returns:
        Cleaned text content from all pages
    """
    reader = PdfReader(file_path)
    text_content = []
    
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_content.append(text)
    
    raw_text = "\n".join(text_content)
    return sanitize_text(raw_text)
```

**Text Sanitization:**
- Remove excessive whitespace via regex
- Strip page numbers and headers
- Normalize encoding artifacts

### 5.2 Skill Extraction Heuristics

The system employs keyword-based skill extraction against a predefined taxonomy:

$$\text{Skills}_{\text{extracted}} = \{s \in \text{Taxonomy} : s \in \text{lowercase}(\text{ResumeText})\}$$

This deterministic approach ensures consistent skill identification across varied resume formats.

---

## 6. Generative AI Integration

### 6.1 The Triple-Provider Architecture

The system implements a **Cascading Fallback Pattern** for AI provider resilience:

```python
AI_FALLBACK_ORDER = [
    ("gemini", "gemini-2.5-flash"),      # Primary
    ("groq", "llama-3.3-70b-versatile"), # Secondary  
    ("ollama", "gemma3:4b")              # Tertiary (Local)
]

def get_ai_analysis(prompt: str) -> str:
    """
    Attempt analysis through each provider in order.
    Raises exception only if all providers fail.
    """
    for provider, model in AI_FALLBACK_ORDER:
        try:
            return call_provider(provider, model, prompt)
        except ProviderError as e:
            logger.warning(f"{provider} failed: {e}")
            continue
    raise AllProvidersFailedError()
```

**Availability Analysis:**
- With 3 independent providers at 95% individual availability:
- Combined availability: $1 - (0.05)^3 = 99.9875\%$

### 6.2 Prompt Engineering Strategy

The quality of LLM output depends entirely on prompt design. We use a **Role-Playing, Context-Bound** structure:

```
SYSTEM PROMPT:
"You are Placify, an expert career counselor for the Central India region.

INPUT CONTEXT:
- Student Profile: {resume_text + quiz_responses}
- Matched Local Opportunities (Verified Data): {matched_companies_json}

TASK:
Based ONLY on the provided Matched Opportunities, generate a career report:
1. Gap Analysis: Compare student skills against company tech_stack
2. Recommendation: Select best company fit with justification
3. Action Plan: Provide specific next steps

OUTPUT FORMAT:
Structured Markdown with clear sections."
```

### 6.3 Hallucination Mitigation

By explicitly constraining the LLM with "Based ONLY on the provided Matched Opportunities," we minimize fabrication risk. The architecture ensures:
- **Facts** (Company Data) come from verified JSON
- **Reasoning** (Why is this a good fit?) comes from the LLM
- **Contact Information** is never generated, only retrieved

---

## 7. Reporting and Visualization

### 7.1 PDF Generation Architecture

The `FPDF` library enables programmatic PDF creation with precise layout control.

**Report Structure:**
1. **Header:** Placify Branding, Generation Date
2. **Executive Summary:** AI-generated overview
3. **Matched Companies:** Ranked list with scores
4. **Skill Gap Analysis:** Strengths and areas for improvement
5. **Action Plan:** Specific recommendations
6. **Footer:** Prototype disclaimer

**Implementation:**
```python
from fpdf import FPDF

class PlacifyReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "PLACIFY ANALYSIS REPORT", ln=True, align="C")
    
    def chapter_title(self, title: str):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, ln=True, fill=True)
    
    def chapter_body(self, content: str):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 6, content)
```

---

## 8. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  index.html │  │  style.css  │  │  script.js  │             │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘             │
│         │              HTTP/REST          │                     │
└─────────┼─────────────────────────────────┼─────────────────────┘
          │                                 │
          ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER (FastAPI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  /api/      │  │  /api/      │  │  /api/      │             │
│  │  upload     │  │  analyze    │  │  download   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ResumeService│  │ AIService    │  │ PDFService   │          │
│  │ (PyPDF2)     │  │ (Gemini/Groq)│  │ (FPDF)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │MatchingService│                           │
│                    │(TF-IDF+LLM)   │                           │
│                    │(scikit-learn) │                           │
│                    └───────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ web_data/    │  │ company_     │  │ web_data/    │          │
│  │ resume/      │  │ dataset/     │  │ analysis/    │          │
│  │ (PDF files)  │  │ (JSON)       │  │ (JSON)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Timeline

| Phase | Duration | Key Deliverables |
| :--- | :--- | :--- |
| **Phase 1: Foundation & Data** | Weeks 1-2 | Dataset curation (94+ companies), JSON schema design, environment setup |
| **Phase 2: Backend Core** | Week 3 | FastAPI setup, Matching algorithm implementation, Service layer architecture |
| **Phase 3: AI Integration** | Week 4 | Triple-provider fallback system, Prompt engineering, Response parsing |
| **Phase 4: Frontend** | Week 5 | HTML/CSS/JS interface, File upload handling, Results display |
| **Phase 5: PDF Generation** | Week 6 | FPDF integration, Report templating, Download functionality |
| **Phase 6: Testing & Polish** | Weeks 7-8 | End-to-end testing, Error handling, Documentation |

---

## 10. Coordinator Talking Points: Defending the Project

### 10.1 Anticipated Critiques and Responses

**1. Critique: "Why didn't you use a standard Vector Database like Pinecone?"**

*Defense:* "We implemented a Hybrid Matching Algorithm that offers superior interpretability for our use case. For a dataset of 94 companies, a vector database introduces unnecessary infrastructure complexity. Our three-stage pipeline (Hard Filters → Scoring → LLM Ranking) provides transparent, explainable matching decisions—crucial for career recommendations where students need to understand 'why' a company is recommended."

**2. Critique: "How is this different from just asking ChatGPT?"**

*Defense:* "ChatGPT provides generic advice. Placify provides **grounded** advice specific to the Central India market. Our system retrieves verified local data—real companies in Indore and Bhopal with validated contact emails—and constrains the LLM to use that context. A generic LLM cannot recommend 'Systematix Infotech in Indore' or provide its specific HR email; Placify can, because it retrieves from a verified knowledge base."

**3. Critique: "The system has no login. Isn't that a security flaw?"**

*Defense:* "It is a **privacy feature**, not a flaw. By designing a stateless architecture with local file storage, we ensure that sensitive student data is stored only on the local machine, not in cloud databases. This 'Privacy by Design' approach minimizes liability and is ideal for a campus tool where data retention policies are strict."

**4. Critique: "What happens if the AI API fails?"**

*Defense:* "We implemented a Triple-Provider Fallback System. If Gemini fails, we automatically switch to Groq. If Groq fails, we fall back to local Ollama. With three independent providers, our theoretical availability is 99.9875%. The system degrades gracefully rather than failing completely."

**5. Critique: "What is the algorithmic complexity here?"**

*Defense:* "The complexity lies in the Multi-Modal Integration. We orchestrate:
- Structured quiz data processing
- Unstructured resume text extraction (NLP)
- Multi-stage matching algorithm
- LLM-powered analysis generation
- Programmatic PDF rendering

The three-stage matching pipeline has complexity $O(n)$ for filtering, $O(n \log n)$ for scoring/sorting, and $O(k)$ for LLM ranking of top-$k$ candidates."

### 10.2 Key Innovation Points

1. **Hybrid Matching:** Combines deterministic filtering with probabilistic LLM reasoning
2. **Triple Fallback:** Ensures high availability without single points of failure
3. **Local-First:** Runs entirely on developer machine with no cloud dependencies
4. **Grounded Generation:** LLM outputs constrained by verified local data
5. **Privacy by Design:** No user accounts, local storage only

---

## 11. Technical Specifications Summary

| Component | Specification |
|-----------|---------------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI 0.100+ |
| **AI Providers** | Gemini 2.5, Groq LLaMA 3.3, Ollama Gemma3 |
| **ML Library** | scikit-learn (TF-IDF, Cosine Similarity) |
| **PDF Library** | FPDF |
| **Resume Parser** | PyPDF2 |
| **Frontend** | HTML5, CSS3, ES6+ JavaScript |
| **Data Format** | JSON |
| **Storage** | File-based (web_data/) |
| **Company Dataset** | 94+ verified entries |
| **Target Region** | Indore-Bhopal-Jabalpur IT Corridor |

---

## 12. Conclusion

This blueprint provides a rigorous, coherent implementation of 'Placify' as a functional prototype. By combining theoretical foundations of information retrieval with practical hybrid matching algorithms, the project demonstrates:

1. **Technical Depth:** Multi-stage matching with mathematical foundations
2. **Engineering Quality:** Fault-tolerant AI integration with cascading fallbacks
3. **Practical Value:** Real recommendations from verified local company data
4. **Privacy Focus:** Stateless design with local-only data storage

The system serves as a potent demonstration of how modern AI technologies can be democratized to solve hyper-local problems in the education sector, specifically addressing the placement challenges faced by engineering graduates in Central India's emerging technology hubs.

---

## Appendix A: Mathematical Notation Reference

| Symbol | Meaning |
|--------|---------|
| $\vec{v}$ | Vector representation of text |
| $\mathbb{R}^n$ | n-dimensional real number space |
| $\mathbf{A} \cdot \mathbf{B}$ | Dot product of vectors A and B |
| $\|\mathbf{A}\|$ | Magnitude (L2 norm) of vector A |
| $O(n)$ | Linear time complexity |
| $k$ | Number of top candidates for LLM ranking |

## Appendix B: API Endpoint Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve main application UI |
| `/api/upload-resume` | POST | Upload and process PDF resume |
| `/api/analyze` | POST | Run full analysis pipeline |
| `/api/quiz` | GET | Retrieve quiz questions |
| `/api/companies` | GET | List all companies in dataset |
| `/api/download-pdf/{id}` | GET | Download generated PDF report |

## Appendix C: File Structure

```
Placify/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── app/
│   ├── config.py           # Configuration and paths
│   ├── database.py         # DB setup and seeding
│   ├── db_models.py        # SQLAlchemy models
│   ├── models.py           # Pydantic data models
│   ├── quiz.py             # Quiz question definitions
│   ├── routes/
│   │   ├── api.py          # REST API endpoints
│   │   └── views.py        # HTML template serving
│   └── services/
│       ├── ai_service.py       # AI provider integration
│       ├── matching_service.py # Company matching logic
│       ├── pdf_service.py      # PDF report generation
│       └── resume_service.py   # Resume text extraction
├── company_dataset/
│   └── companies.json      # 94+ verified companies
├── docs/                   # Developer & API documentation
├── image/
│   └── placify_logo.svg    # Unified vector logo
├── nginx/                  # Nginx proxy configuration
├── notebooks/              
│   └── quick_demo.ipynb    # Hybrid engine demo for evaluators
├── static/                 # Custom CSS and JavaScript
├── template/               # HTML templates
│   ├── index.html          # Main application page
│   ├── privacy-policy.html # Privacy Policy page
│   └── terms.html          # Terms & Conditions page
├── web_data/
│   ├── resume/             # Uploaded PDF resumes
│   ├── analysis/           # JSON analysis results
│   └── pdf/                # Generated PDF reports
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Multi-container orchestration
```
