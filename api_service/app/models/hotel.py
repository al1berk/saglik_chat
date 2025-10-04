# Otel veritabanı modeli
from sqlalchemy import Column, Integer, String, Float, Text
from app.db.session import Base

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city = Column(String, index=True)
    address = Column(Text)
    rating = Column(Float)
    price_per_night = Column(Float)
    phone = Column(String)
    email = Column(String)
    description = Column(Text)
    distance_to_clinic = Column(Float)  # Kliniğe uzaklık (km)
