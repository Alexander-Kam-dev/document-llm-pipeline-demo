"""Configuration management for the document processing pipeline."""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Extraction Mode
    extraction_mode: str = os.getenv("EXTRACTION_MODE", "llm")
    
    # Storage Paths
    sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", "./data/documents.db")
    json_output_dir: str = os.getenv("JSON_OUTPUT_DIR", "./data/outputs")
    
    # OCR Configuration
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
    
    model_config = ConfigDict(env_file=".env")


settings = Settings()
