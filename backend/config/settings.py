import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "CareCoord - Agentic Healthcare Workflow System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # SQLite Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./carecoord.db")

settings = Settings()
