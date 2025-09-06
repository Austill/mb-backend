import os
from dotenv import load_dotenv

# Load environment variables from a .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-for-dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI")  # ✅ now uses DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    }
    # Allow CORS from your Vercel frontend and local dev
    # The string is split by commas in __init__.py
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://mb-frontend-rho.vercel.app,http://localhost:3000"
    )
