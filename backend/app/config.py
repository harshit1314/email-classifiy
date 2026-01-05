"""
Configuration settings for the application
"""
import os
from typing import Dict

class Config:
    """Application configuration"""
    
    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Database Settings
    DATABASE_PATH = os.getenv("DATABASE_PATH", "email_classifications.db")
    
    # Email Server Settings
    GMAIL_ENABLED = os.getenv("GMAIL_ENABLED", "false").lower() == "true"
    OUTLOOK_ENABLED = os.getenv("OUTLOOK_ENABLED", "false").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    
    # ML Model Settings
    MODEL_PATH = os.getenv("MODEL_PATH", "app/ml/email_classifier_model.joblib")
    
    # OpenAI/LLM Settings (DISABLED - using BERT only)
    OPENAI_API_KEY = ""
    OPENAI_MODEL = "gpt-3.5-turbo"
    USE_LLM = False  # Disabled - using BERT/TF-IDF classifier
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # MongoDB Settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "ai_email")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "classifications")
    # Separate collection for raw ingested emails (optional)
    MONGO_INGEST_COLLECTION = os.getenv("MONGO_INGEST_COLLECTION", "ingested_emails")
    # Retention days (set to 0 to disable TTL index)
    MONGO_RETENTION_DAYS = int(os.getenv("MONGO_RETENTION_DAYS", "0"))

