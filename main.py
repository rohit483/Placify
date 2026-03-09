import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR, COMPANIES_FILE
from app.database import init_db, seed_companies_from_json
from app.routes import api, views

app = FastAPI()

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()
    print("Database tables created / verified.")
    seed_companies_from_json(str(COMPANIES_FILE))

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include Routers
app.include_router(api.router)
app.include_router(views.router)

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
