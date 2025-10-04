# Otel CRUD işlemleri (Create, Read, Update, Delete)
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate

def get_hotel(db: Session, hotel_id: int) -> Optional[Hotel]:
    """Belirli bir oteli getir"""
    return db.query(Hotel).filter(Hotel.id == hotel_id).first()

def get_hotels(db: Session, skip: int = 0, limit: int = 100) -> List[Hotel]:
    """Tüm otelleri listele"""
    return db.query(Hotel).offset(skip).limit(limit).all()

def create_hotel(db: Session, hotel: HotelCreate) -> Hotel:
    """Yeni otel oluştur"""
    db_hotel = Hotel(**hotel.dict())
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

def search_hotels(
    db: Session,
    city: Optional[str] = None,
    min_rating: Optional[float] = None
) -> List[Hotel]:
    """Otel ara"""
    query = db.query(Hotel)
    
    if city:
        query = query.filter(Hotel.city.ilike(f"%{city}%"))
    if min_rating:
        query = query.filter(Hotel.rating >= min_rating)
    
    return query.all()
