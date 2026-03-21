import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Engine and session are created lazily to avoid crashing at import
# when DATABASE_URL has not yet been injected (e.g. before Docker env init)
_engine = None
SessionLocal = None

def _get_engine():
    global _engine, SessionLocal
    if _engine is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Make sure your .env file is loaded or env_file is configured in docker-compose."
            )
        ssl_args = {"sslmode": "require"} if "neon.tech" in DATABASE_URL else {}
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=ssl_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

# ------------- Function to get DB session for FastAPI dependency injection ---------------
def get_db():
    """FastAPI dependency that yields a DB session."""
    _get_engine()  # ensure engine is initialised
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Function to initialize database tables -----------------------
def init_db():
    """Create all tables. Call once at startup."""
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)


# --------- Function to seed companies from JSON file into PostgreSQL -----------
def seed_companies_from_json(json_path: str):
    """Sync companies from JSON to database (incremental).
    
    - Adds new companies (by name+role match)
    - Skips existing companies
    - Never deletes or updates existing records
    
    Set SKIP_SEED=true in production to disable seeding entirely.
    """
    from app.db_models import Company

    # Production safety: explicit skip via env var
    if os.getenv("SKIP_SEED", "").lower() == "true":
        print("SKIP_SEED=true, skipping company seed.")
        return

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Cannot seed companies.")
        return

    _get_engine()
    db = SessionLocal()
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            companies = json.load(f)

        # Get existing name+role pairs for quick lookup
        existing = db.query(Company.name, Company.role).all()
        existing_set = {(name.lower().strip(), role.lower().strip()) for name, role in existing}

        added = 0
        skipped = 0

        for c in companies:
            name = c["name"].strip()
            role = c["role"].strip()
            key = (name.lower(), role.lower())

            if key in existing_set:
                skipped += 1
                continue

            record = Company(
                name=name,
                role=role,
                location=c.get("location", ""),
                email=c.get("email", ""),
                skills=c.get("skills", []),
                description=c.get("description", ""),
            )
            db.add(record)
            existing_set.add(key)  # Prevent duplicates within same JSON
            added += 1

        db.commit()
        
        if added > 0:
            print(f"Seeded {added} new companies from {json_path}")
        if skipped > 0:
            print(f"Skipped {skipped} existing companies")
        if added == 0 and skipped > 0:
            print("All companies already in database, nothing to add.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding companies: {e}")
    finally:
        db.close()
