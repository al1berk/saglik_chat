# api_service/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sys
import os

# MongoDB logger'ı import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_service.mongodb_logger import MongoDBLogger

app = FastAPI(title="Health Tourism API", version="1.0.0")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB logger instance
mongo_logger = MongoDBLogger()

# ============ MODELS ============
class Clinic(BaseModel):
    id: int
    name: str
    address: str
    city: str
    district: str
    treatments: List[str]
    rating: float
    accreditations: List[str]
    languages: List[str]
    price_range: str

class Hotel(BaseModel):
    id: int
    name: str
    region: str
    stars: int
    features: List[str]
    price_per_night: int
    currency: str

class SearchRequest(BaseModel):
    treatment: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    budget: Optional[int] = None

# ============ MOCK DATABASE ============
CLINICS_DB = [
    {
        "id": 1,
        "name": "Antmodern Oral & Dental Health Clinic",
        "address": "Fener Mah. Bülent Ecevit Blv. No:50 Muratpaşa/Antalya",
        "city": "Antalya",
        "district": "Muratpaşa",
        "treatments": ["Dental Implant", "Teeth Whitening", "Veneers"],
        "rating": 4.8,
        "accreditations": ["JCI", "ISO 9001"],
        "languages": ["Turkish", "English", "Russian"],
        "price_range": "medium"
    },
    {
        "id": 2,
        "name": "Dr. Gökhan Özerdem Clinic",
        "address": "Yeşilbahçe Mah. Metin Kasapoğlu Cad. No: 48/11",
        "city": "Antalya",
        "district": "Muratpaşa",
        "treatments": ["Rhinoplasty", "Face Lift", "Breast Surgery"],
        "rating": 4.9,
        "accreditations": ["JCI", "ISAPS"],
        "languages": ["Turkish", "English", "Arabic"],
        "price_range": "premium"
    }
]

HOTELS_DB = [
    {
        "id": 1,
        "name": "Delphin Palace",
        "region": "Lara",
        "stars": 5,
        "features": ["Spa", "Pool", "All Inclusive", "Beach"],
        "price_per_night": 200,
        "currency": "EUR"
    },
    {
        "id": 2,
        "name": "Regnum Carya Golf & Spa Resort",
        "region": "Belek",
        "stars": 5,
        "features": ["Spa", "Golf", "Pool"],
        "price_per_night": 350,
        "currency": "EUR"
    }
]

# ============ ENDPOINTS ============
@app.get("/")
def root():
    return {"message": "Health Tourism API v1.0", "status": "running"}

@app.post("/api/clinics/search")
def search_clinics(request: SearchRequest):
    """Klinik arama"""
    results = CLINICS_DB.copy()
    
    if request.city:
        results = [c for c in results if c["city"].lower() == request.city.lower()]
    
    if request.treatment:
        treatment_lower = request.treatment.lower()
        results = [c for c in results if any(treatment_lower in t.lower() for t in c["treatments"])]
    
    return {
        "total": len(results),
        "results": results
    }

@app.get("/api/clinics/{clinic_id}")
def get_clinic_details(clinic_id: int):
    """Klinik detayları"""
    clinic = next((c for c in CLINICS_DB if c["id"] == clinic_id), None)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic

@app.post("/api/hotels/search")
def search_hotels(request: SearchRequest):
    """Otel arama"""
    results = HOTELS_DB.copy()
    
    if request.region:
        results = [h for h in results if h["region"].lower() == request.region.lower()]
    
    if request.budget:
        results = [h for h in results if h["price_per_night"] <= request.budget]
    
    return {
        "total": len(results),
        "results": results
    }

@app.post("/api/packages/generate")
def generate_package(
    treatment: str,
    city: str,
    budget: int,
    nights: int = 7
):
    """Paket önerisi oluştur"""
    # Klinikleri filtrele
    clinics = [c for c in CLINICS_DB if c["city"].lower() == city.lower()]
    
    # Otelleri filtrele
    hotels = HOTELS_DB.copy()
    
    packages = []
    for i, clinic in enumerate(clinics[:3]):
        hotel = hotels[i % len(hotels)]
        
        treatment_price = 2000 if clinic["price_range"] == "medium" else 3500
        hotel_cost = hotel["price_per_night"] * nights
        flight_cost = 600
        transfer_cost = 150
        
        total = treatment_price + hotel_cost + flight_cost + transfer_cost
        
        if total <= budget:
            packages.append({
                "package_id": i + 1,
                "clinic": clinic,
                "hotel": hotel,
                "costs": {
                    "treatment": treatment_price,
                    "hotel": hotel_cost,
                    "flight": flight_cost,
                    "transfer": transfer_cost,
                    "total": total
                },
                "nights": nights
            })
    
    return {
        "total_packages": len(packages),
        "packages": packages
    }

# ============ MONGODB ENDPOINTS ============
@app.get("/api/conversations/{user_id}")
def get_user_conversations(user_id: str, limit: int = 50):
    """Kullanıcının conversation geçmişini getir"""
    try:
        conversations = mongo_logger.get_user_conversations(user_id, limit)
        return {
            "user_id": user_id,
            "total": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/{user_id}")
def get_user_profile(user_id: str):
    """Kullanıcı profilini getir"""
    try:
        user = mongo_logger.get_user(user_id)
        if not user:
            return {
                "user_id": user_id,
                "message": "User not found",
                "profile": None
            }
        return {
            "user_id": user_id,
            "profile": user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile/{user_id}")
def update_user_profile(user_id: str, profile_data: dict):
    """Kullanıcı profilini güncelle"""
    try:
        profile_data["user_id"] = user_id
        mongo_logger.upsert_user(profile_data)
        return {
            "status": "success",
            "message": "Profile updated",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/intents")
def get_intent_statistics(days: int = 30):
    """Intent istatistikleri"""
    try:
        stats = mongo_logger.get_intent_statistics(days)
        return {
            "period_days": days,
            "intent_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/users")
def get_active_users(days: int = 7):
    """Aktif kullanıcı sayısı"""
    try:
        count = mongo_logger.get_active_users(days)
        total_conversations = mongo_logger.get_total_conversations()
        return {
            "period_days": days,
            "active_users": count,
            "total_conversations": total_conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Sistem sağlık kontrolü"""
    mongo_health = mongo_logger.health_check()
    return {
        "status": "healthy",
        "service": "api",
        "mongodb": "connected" if mongo_health else "disconnected"
    }

# Cleanup on shutdown
@app.on_event("shutdown")
def shutdown_event():
    mongo_logger.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")