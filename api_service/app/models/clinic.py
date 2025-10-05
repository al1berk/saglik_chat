# Klinik veritabanı modeli
from sqlalchemy import Column, Integer, String, Float, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(String, primary_key=True, index=True)  # JSON'dan gelen ID (ant_clinic_001)
    name = Column(String, index=True, nullable=False)
    city = Column(String, index=True, nullable=False)
    country = Column(String, default="Turkey")
    address = Column(Text)
    rating = Column(Float, index=True)
    phone = Column(String)
    treatments = Column(JSON)  # Array of strings: ["Composite Bonding", "Zirconium Crowns"]
    
    # Metadata
    created_at = Column(String)  # ISO format date
    updated_at = Column(String)  # ISO format date
    
    # Relationships
    appointments = relationship("Appointment", back_populates="clinic", cascade="all, delete-orphan")

