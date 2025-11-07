import os
import logging
from dotenv import load_dotenv

# Load environment variables from a .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-for-dev")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/mindbuddy")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mind_buddy")
    FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
    FLW_SIGNATURE_KEY = os.getenv("FLW_SIGNATURE_KEY")
    FLW_PLAN_ID = os.getenv("FLW_PLAN_ID")
    REDIRECT_URL = os.getenv("REDIRECT_URL")
    # Allow CORS from your Vercel frontend and local dev
    # The string is split by commas in __init__.py
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://mb-frontend-rho.vercel.app,http://localhost:8080"
    )

    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Logging configuration
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")
    LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # LLM configuration
    HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "facebook/blenderbot-400M-distill")
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "100"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
