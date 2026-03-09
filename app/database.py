import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------- Function to get DB session for FastAPI dependency injection ---------------
def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Function to initialize database tables -----------------------
def init_db():
    """Create all tables. Call once at startup."""
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
