# Klinikler ile ilgili endpointler
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.clinic import Clinic, ClinicCreate
from app.crud import crud_clinic
from app.services.search_service import search_service

router = APIRouter()

@router.get("/search", response_model=List[dict])
async def search_clinics(
    q: Optional[str] = Query(None, description="Arama metni"),
    city: Optional[str] = Query(None, description="Şehir filtresi"),
    treatment: Optional[str] = Query(None, description="Tedavi türü"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum puan"),
    limit: int = Query(5, ge=1, le=50, description="Maksimum sonuç sayısı")
):
    """
    ChromaDB ile klinik ara
    
    - **q**: Genel arama metni
    - **city**: Şehir filtresi (örn: Antalya, İstanbul)
    - **treatment**: Tedavi türü (örn: Hair Transplant, Dental)
    - **min_rating**: Minimum puan (0-5 arası)
    - **limit**: Maksimum sonuç sayısı
    """
    try:
        clinics = search_service.search_clinics(
            query=q,
            city=city,
            treatment=treatment,
            min_rating=min_rating,
            limit=limit
        )
        return clinics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Arama sırasında hata oluştu: {str(e)}"
        )

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
