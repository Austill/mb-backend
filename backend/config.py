import os
import logging
from dotenv import load_dotenv

# Load environment variables from a .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-for-dev")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://austin:misaro@cluster1.ynxgjwq.mongodb.net/?appName=Cluster1")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mindbuddy")
    FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
    FLW_SIGNATURE_KEY = os.getenv("FLW_SIGNATURE_KEY")
    FLW_PLAN_ID = os.getenv("FLW_PLAN_ID")
    REDIRECT_URL = os.getenv("REDIRECT_URL")
    # Allow CORS from your Vercel frontend and local dev
    # The string is split by commas in __init__.py
    # Note: include the exact scheme (https://) for deployed Vercel frontend
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "https://mb-frontend-rho.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    )

    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Bcrypt configuration (lower rounds for dev speed)
    BCRYPT_LOG_ROUNDS = int(os.getenv("BCRYPT_LOG_ROUNDS", 8))  # 8 is fast for dev, increase for prod

    # Logging configuration
    # Default to WARNING to reduce log noise in dev. Override with LOGGING_LEVEL env var.
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "WARNING")
    LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Groq API configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
