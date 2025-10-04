# Klinikler ile ilgili endpointler
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.clinic import Clinic, ClinicCreate
from app.crud import crud_clinic

router = APIRouter()

@router.get("/", response_model=List[Clinic])
def get_clinics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Tüm klinikleri listele"""
    clinics = crud_clinic.get_clinics(db, skip=skip, limit=limit)
    return clinics

@router.get("/{clinic_id}", response_model=Clinic)
def get_clinic(
    clinic_id: int,
    db: Session = Depends(get_db)
):
    """Belirli bir kliniği getir"""
    clinic = crud_clinic.get_clinic(db, clinic_id=clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Klinik bulunamadı")
    return clinic

@router.post("/", response_model=Clinic)
def create_clinic(
    clinic: ClinicCreate,
    db: Session = Depends(get_db)
):
    """Yeni klinik oluştur"""
    return crud_clinic.create_clinic(db=db, clinic=clinic)

@router.get("/search/", response_model=List[Clinic])
def search_clinics(
    city: str = None,
    specialty: str = None,
    db: Session = Depends(get_db)
):
    """Klinik ara"""
    return crud_clinic.search_clinics(db, city=city, specialty=specialty)
