# API Router'ı birleştiren dosya
from fastapi import APIRouter
from app.api.endpoints import clinics, hotels, chat

api_router = APIRouter()

api_router.include_router(clinics.router, prefix="/clinics", tags=["clinics"])
api_router.include_router(hotels.router, prefix="/hotels", tags=["hotels"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
