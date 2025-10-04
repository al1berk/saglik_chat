# Klinik veritabanı modeli
from sqlalchemy import Column, Integer, String, Float, Text
from app.db.session import Base

class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city = Column(String, index=True)
    address = Column(Text)
    specialty = Column(String, index=True)  # Uzmanlık alanı
    rating = Column(Float)
    phone = Column(String)
    email = Column(String)
    description = Column(Text)
