# Oteller ile ilgili endpointler
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.hotel import Hotel, HotelCreate
from app.crud import crud_hotel

router = APIRouter()

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

@router.get("/search/", response_model=List[Hotel])
def search_hotels(
    city: str = None,
    min_rating: float = None,
    db: Session = Depends(get_db)
):
    """Otel ara"""
    return crud_hotel.search_hotels(db, city=city, min_rating=min_rating)
