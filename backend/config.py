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
     # Allow CORS from your Vercel frontend and local dev
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://mb-frontend-rho.vercel.app"
    )
