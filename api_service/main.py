# FastAPI uygulamasının başlangıç noktası
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.db.session import Base, engine
import logging

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router'ları ekle
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatılırken ChromaDB'yi warm-up yap"""
    logger.info("🚀 API Service başlatılıyor...")
    
    # ChromaDB'yi warm-up yap (ilk query'de model yüklensin)
    try:
        logger.info("🔥 ChromaDB warm-up başlıyor...")
        from app.services.search_service import search_service
        
        # Dummy search ile model yüklensin
        _ = search_service.search_hotels(city="Antalya", limit=1)
        logger.info("✅ ChromaDB warm-up tamamlandı - sistem hazır!")
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB warm-up hatası (normal): {e}")

@app.get("/")
def root():
    return {"message": "Sağlık Chat API'ye hoş geldiniz!"}

@app.get("/health")
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    return {"status": "healthy", "service": "saglik-chat-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=75,  # Keep-alive timeout
        limit_concurrency=100,  # Eşzamanlı istek limiti
        timeout_graceful_shutdown=5
    )
