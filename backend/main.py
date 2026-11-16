import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.config.settings import settings
from backend.database.database import init_db, get_db
from backend.routes import patients, doctors, appointments, beds, emergencies, dashboard, workflow, auth, notifications, websocket, policies, predictions, optimization, integrations
from backend.realtime.connection_manager import connection_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure DB tables exist on startup and initialize WebSocket loop."""
    init_db()
    try:
        connection_manager.set_loop(asyncio.get_running_loop())
    except Exception:
        pass
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API foundation for CareCoord hospital workflow coordination system.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware setup - Allow frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(doctors.router, prefix=settings.API_V1_STR)
app.include_router(appointments.router, prefix=settings.API_V1_STR)
app.include_router(beds.router, prefix=settings.API_V1_STR)
app.include_router(emergencies.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(workflow.router, prefix=settings.API_V1_STR)
app.include_router(policies.router)
app.include_router(predictions.router)
app.include_router(optimization.router)
app.include_router(integrations.router)
app.include_router(websocket.router)
app.include_router(websocket.router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root endpoint", tags=["System"])
def root():
    """Root backend route providing operational status and links."""
    return {
        "status": "healthy",
        "service": "CareCoord Backend API",
        "version": settings.VERSION,
        "frontend_dashboard": "http://localhost:5173/",
        "swagger_docs": "http://localhost:8000/docs",
        "health_check": "http://localhost:8000/health"
    }


@app.get("/health", summary="Basic health check", tags=["System"])
def health_check():
    """Return system operational status."""
    return {
        "status": "healthy",
        "service": "CareCoord Backend",
        "version": settings.VERSION
    }


@app.get("/health/database", summary="Database health check", tags=["System"])
def database_health_check(db: Session = Depends(get_db)):
    """Verify SQLite database connectivity and return entity counts."""
    try:
        # Test DB connection with a simple query
        db.execute(text("SELECT 1"))
        
        from backend.database.models import Patient, Doctor, Appointment, Bed, Emergency
        return {
            "status": "healthy",
            "database": "SQLite",
            "connected": True,
            "counts": {
                "patients": db.query(Patient).count(),
                "doctors": db.query(Doctor).count(),
                "appointments": db.query(Appointment).count(),
                "beds": db.query(Bed).count(),
                "emergencies": db.query(Emergency).count()
            }
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(exc)}"
        )
