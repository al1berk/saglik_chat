# Proje konfigürasyonları
from pathlib import Path

# Pydantic 1.x ve 2.x uyumluluğu için
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sağlık Chat API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./saglik_chat.db"
    
    # ChromaDB
    CHROMA_DB_PATH: Path = Path(__file__).parent.parent.parent / "storage" / "chroma_db"
    CLINICS_COLLECTION: str = "medical_clinics"
    HOTELS_COLLECTION: str = "medical_hotels"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TEMPERATURE: float = 0.7
    
    # Rasa
    RASA_URL: str = "http://localhost:5005"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings()
