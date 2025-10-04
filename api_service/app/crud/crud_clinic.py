# Klinik CRUD işlemleri (Create, Read, Update, Delete)
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.clinic import Clinic
from app.schemas.clinic import ClinicCreate

def get_clinic(db: Session, clinic_id: int) -> Optional[Clinic]:
    """Belirli bir kliniği getir"""
    return db.query(Clinic).filter(Clinic.id == clinic_id).first()

def get_clinics(db: Session, skip: int = 0, limit: int = 100) -> List[Clinic]:
    """Tüm klinikleri listele"""
    return db.query(Clinic).offset(skip).limit(limit).all()

def create_clinic(db: Session, clinic: ClinicCreate) -> Clinic:
    """Yeni klinik oluştur"""
    db_clinic = Clinic(**clinic.dict())
    db.add(db_clinic)
    db.commit()
    db.refresh(db_clinic)
    return db_clinic

def search_clinics(
    db: Session,
    city: Optional[str] = None,
    specialty: Optional[str] = None
) -> List[Clinic]:
    """Klinik ara"""
    query = db.query(Clinic)
    
    if city:
        query = query.filter(Clinic.city.ilike(f"%{city}%"))
    if specialty:
        query = query.filter(Clinic.specialty.ilike(f"%{specialty}%"))
    
    return query.all()
