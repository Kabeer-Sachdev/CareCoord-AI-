from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config.settings import settings

# For SQLite, check_same_thread=False allows multiple threads to share the connection
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency to yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all database tables defined in models and run lightweight column migrations."""
    from backend.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Lightweight schema sync for existing SQLite database
    with engine.connect() as conn:
        # Check doctors table
        try:
            res = conn.execute(Base.metadata.bind.text if hasattr(Base.metadata, "bind") else __import__("sqlalchemy").text("PRAGMA table_info(doctors)")).fetchall()
            cols = [r[1] for r in res]
            if "availability_status" not in cols:
                conn.execute(__import__("sqlalchemy").text("ALTER TABLE doctors ADD COLUMN availability_status VARCHAR(50) DEFAULT 'Available'"))
                conn.commit()
        except Exception:
            pass

        # Check workflow_runs table
        try:
            res = conn.execute(__import__("sqlalchemy").text("PRAGMA table_info(workflow_runs)")).fetchall()
            cols = [r[1] for r in res]
            if "requested_by" not in cols:
                conn.execute(__import__("sqlalchemy").text("ALTER TABLE workflow_runs ADD COLUMN requested_by VARCHAR(50)"))
                conn.commit()
            if "requested_role" not in cols:
                conn.execute(__import__("sqlalchemy").text("ALTER TABLE workflow_runs ADD COLUMN requested_role VARCHAR(50)"))
                conn.commit()
        except Exception:
            pass
