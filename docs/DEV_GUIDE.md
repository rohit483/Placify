# 🛠️ Placify Developer Guide

Because we have a separate [API.md](../API.md) for endpoints, this guide focuses entirely on **how to run and manage the project** in two environments: 
1. **Local Development** (on your laptop)
2. **Production Deployment** (cloud servers).

---

## 💻 1. Local Development (Your Laptop)
*Use this environment when writing code, building new features, or testing before pushing to GitHub.*

### Option A: Standard Python Way (Easiest for quick coding)
This skips Docker entirely and runs the app barebones on your machine using a local SQLite database by default (if `DATABASE_URL` is unset).
1. **Setup Environment**:
   ```bash
   python -m venv venv
   # Windows: .\venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Set Minimum Env Vars** (in your `.env` file):
   ```ini
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   # Optional: Set DATABASE_URL if you want to test against Neon locally
   ```
3. **Run the App**:
   ```bash
   python main.py
   # Go to http://127.0.0.1:8000
   ```

### Option B: Full Docker Stack (Best for testing production parity)
This spins up the FastAPI app **and** a local PostgreSQL database container exactly how it would run in production.
1. **Fill out `.env`**: Make sure your `.env` has your API keys.
2. **Start Everything**:
   ```bash
   docker-compose up --build
   ```
3. **Resetting your local DB**:
   If you mess up your local database during testing, just destroy the container and the data volume:
   ```bash
   docker-compose down -v
   ```

---

## ☁️ 2. Production Deployment (Live Server)
*Use this when your code is tested and you are pushing the `main` branch live to Render + Neon.*

> **Architecture Note**: In production, we actually **do not** use `docker-compose.yml` or the `nginx` folder. The cloud provider (Render) handles Nginx routing for us automatically and only looks at the `Dockerfile`.

### The Deployment Flow
1. **Commit and Push**:
   ```bash
   git add -A
   git commit -m "Update feature X"
   git push origin main
   ```
2. **Render Auto-Deploys**: Render detects the new push, rebuilds your Docker image from `Dockerfile`, and starts the server. 
3. **Database Seeding**: On app startup, `seed_companies_from_json()` reads `companies.json` and ensures any new companies are added to the Neon Database automatically.

### Production Environment Variables (Set in Render Dashboard)
| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://...` | Must be your **Pooled Connection String** from Neon. SSL mode is auto-handled by the app. |
| `GEMINI_API_KEY` | `...` | Required |
| `GROQ_API_KEY`   | `...` | Required |
| `SKIP_SEED`      | `false` / `true` | Set to `false` when deploying new JSON data, then switch to `true` to speed up future restarts. |
| `ADMIN_SECRET`   | `any_secure_password` | Protects your POST `/api/admin/reseed` endpoint. |

### Post-Deployment Data Management
Once on Render, avoid changing data directly in `companies.json` if possible (unless you are doing a massive bulk update). Instead:
1. **Manual Editing**: Connect a database tool like **DBeaver** or **TablePlus** directly to your Neon database using the Neon Direct URL.
2. **Bulk Adding**: Add new companies to `companies.json`, push to GitHub, and hit your production `POST /api/admin/reseed?secret=YOUR_SECRET` endpoint to tell the server to inject the new records without deleting old ones.
