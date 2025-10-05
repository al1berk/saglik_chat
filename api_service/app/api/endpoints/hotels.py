# Oteller ile ilgili endpointler
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.hotel import Hotel, HotelCreate
from app.crud import crud_hotel
from app.services.search_service import search_service

router = APIRouter()

@router.get("/search", response_model=List[dict])
async def search_hotels(
    q: Optional[str] = Query(None, description="Arama metni"),
    city: Optional[str] = Query(None, description="Şehir filtresi"),
    hotel_type: Optional[str] = Query(None, description="Otel tipi"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum puan"),
    max_price: Optional[float] = Query(None, ge=0, description="Maksimum fiyat"),
    limit: int = Query(5, ge=1, le=50, description="Maksimum sonuç sayısı")
):
    """
    ChromaDB ile otel ara
    
    - **q**: Genel arama metni
    - **city**: Şehir filtresi (örn: Antalya, İstanbul)
    - **hotel_type**: Otel tipi (örn: Medical Hotel, Recovery Hotel)
    - **min_rating**: Minimum puan (0-5 arası)
    - **max_price**: Maksimum gecelik fiyat ($)
    - **limit**: Maksimum sonuç sayısı
    """
    try:
        hotels = search_service.search_hotels(
            query=q,
            city=city,
            hotel_type=hotel_type,
            min_rating=min_rating,
            max_price=max_price,
            limit=limit
        )
        return hotels
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Arama sırasında hata oluştu: {str(e)}"
        )

@router.get("/", response_model=List[Hotel])
def get_hotels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Tüm otelleri listele"""
    hotels = crud_hotel.get_hotels(db, skip=skip, limit=limit)
    return hotels

@router.get("/{hotel_id}", response_model=Hotel)
def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    """Belirli bir oteli getir"""
    hotel = crud_hotel.get_hotel(db, hotel_id=hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="Otel bulunamadı")
    return hotel

@router.post("/", response_model=Hotel)
def create_hotel(
    hotel: HotelCreate,
    db: Session = Depends(get_db)
):
    """Yeni otel oluştur"""
    return crud_hotel.create_hotel(db=db, hotel=hotel)
