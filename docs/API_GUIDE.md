# 🗺️ Placify API Documentation

This document outlines all the available API endpoints in the Placify application. Because Placify is built on **FastAPI**, an interactive, auto-generated version of this documentation is always available by running the app and navigating to `/docs` (e.g., `http://localhost:8000/docs`).

---

## 🚀 Core API (Used by Frontend)

### `GET /api/questions/{mode}`
- **Purpose**: Fetches the interview questions for the user based on the selected mode.
- **Modes**: `fast` (quick test) or `detailed` (comprehensive test).

### `POST /api/upload_resume`
- **Purpose**: Uploads and extracts text from the user's resume PDF.
- **Payload**: `multipart/form-data` with `file: <pdf>`.

### `POST /api/assess`
- **Purpose**: Runs the core AI matching engine to grade the user's answers and recommend matching companies.
- **Payload**: JSON containing extracted resume text, selected mode, and structured Q&A answers.

### `GET /api/report/pdf`
- **Purpose**: Downloads the final assessment report as a formatted PDF file.

---

## 🔒 Administration

### `POST /api/admin/reseed`
- **Purpose**: Securely updates the product database by dynamically injecting new entries found in `companies.json` directly into the Postgres database. Old data is preserved.
- **Query Params**: `secret` (Must match the `ADMIN_SECRET` environment variable, or `default_dev_secret` if unset).

---

## 🛠️ Developer & Debugging (CRUD)
*These endpoints are used for reading and manually modifying internal database tables. They are extremely useful when testing the UI in `/docs`.*

### Companies Table
- `GET /api/dev/companies` — Lists all companies in the DB.
- `POST /api/dev/companies` — Adds a single new company manually.
- `GET /api/dev/companies/search` — Searches for companies by name or role.
- `GET /api/dev/companies/{id}` — Gets details for a specific company ID.
- `PUT /api/dev/companies/{id}` — Updates/edits a specific company ID.
- `DELETE /api/dev/companies/{id}` — Deletes a specific company ID.

### Resumes Table
- `GET /api/dev/resumes` — Lists all uploaded resumes.
- `GET /api/dev/resumes/search` — Search resumes by filename.
- `GET /api/dev/resumes/{id}/text` — Returns the raw extracted text of a past resume.
- `GET /api/dev/resumes/{id}/pdf` — Downloads the original PDF of a past resume.

### Assessments Table
- `GET /api/dev/assessments` — Lists all past AI assessment runs and their generated match scores.
- `GET /api/dev/assessments/{id}` — Views a specific assessment's full JSON results.
- `GET /api/dev/assessments/{id}/pdf` — Re-downloads the PDF report for a specific past assessment.

---

## 🌐 Next Steps

To test these right now without leaving your browser or using Postman:
1. Run `docker-compose up` or `python main.py`
2. Open **[http://localhost:8000/docs](http://localhost:8000/docs)**
