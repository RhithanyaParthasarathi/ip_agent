"""Configuration settings for the RAG agent."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys (optional - only needed if using cloud models)
    google_api_key: str = ""
    
    # Qdrant Settings
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    vector_collection: str = "company_docs"
    
    # Application Settings
    app_name: str = "Company RAG Agent"
    upload_dir: Path = Path("./data/uploads")
    
    # Ollama Settings (local LLM)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"  # Llama 3.2 1B - small but newer architecture
    
    # Embedding Model (local, runs via sentence-transformers)
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    # Azure Communication Services
    acs_connection_string: str = ""
    
    # Azure AD / Bot
    azure_app_id: str = ""
    azure_app_secret: str = ""
    azure_tenant_id: str = ""
    
    # Bot callback URL (ngrok URL in dev)
    bot_callback_url: str = "http://localhost:8000"
    
    # Google Cloud Speech (optional - for STT/TTS)
    google_cloud_project_id: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
settings = Settings()

# Create upload directory if it doesn't exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)

