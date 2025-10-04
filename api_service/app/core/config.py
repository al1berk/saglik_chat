# Proje konfigürasyonları
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sağlık Chat API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./saglik_chat.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings()
