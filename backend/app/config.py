"""Configuration settings for the RAG agent."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    google_api_key: str
    
    # Qdrant Settings
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    vector_collection: str = "company_docs"
    
    # Application Settings
    app_name: str = "Company RAG Agent"
    upload_dir: Path = Path("./data/uploads")
    
    # Model Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    gemini_model: str = "gemini-2.5-flash"
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
settings = Settings()

# Create upload directory if it doesn't exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
