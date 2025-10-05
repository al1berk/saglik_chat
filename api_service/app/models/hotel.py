# Otel veritabanı modeli
from sqlalchemy import Column, Integer, String, Float, Text, JSON
from app.db.session import Base

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(String, primary_key=True, index=True)  # JSON'dan gelen ID (hotel_001)
    name = Column(String, index=True, nullable=False)
    city = Column(String, index=True, nullable=False)
    country = Column(String, default="Turkey")
    address = Column(Text)
    rating = Column(Float, index=True)
    price_per_night = Column(Float)
    phone = Column(String)
    features = Column(JSON)  # Array: ["Spa", "Pool", "Airport Transfer"]
    amenities = Column(JSON)  # Array: ["WiFi", "Restaurant", "Gym"]
    
    # Metadata
    created_at = Column(String)  # ISO format date
    updated_at = Column(String)  # ISO format date

