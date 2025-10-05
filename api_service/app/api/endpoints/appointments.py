"""
Appointment API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentStatus
)
from app.crud import crud_appointment
from app.crud.crud_clinic import get_clinic

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni randevu oluştur
    
    **Gerekli Alanlar:**
    - customer_name: Müşteri adı
    - customer_email: Email
    - customer_phone: Telefon
    - clinic_id: Klinik ID
    - treatment_name: Tedavi adı
    - preferred_date: İstenen tarih (ISO format: 2025-10-15T10:00:00)
    
    **Opsiyonel Alanlar:**
    - customer_country: Ülke
    - customer_language: Dil (tr, en, de, ar, ru, nl)
    - alternative_date: Alternatif tarih
    - notes: Müşteri notları
    - estimated_price: Tahmini fiyat
    """
    # Klinik var mı kontrol et
    clinic = get_clinic(db, appointment.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail=f"Clinic {appointment.clinic_id} not found")
    
    # Randevu oluştur
    db_appointment = crud_appointment.create_appointment(db, appointment)
    
    return db_appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db)
):
    """
    ID'ye göre randevu detayını getir
    """
    appointment = crud_appointment.get_appointment(db, appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment


@router.get("/", response_model=AppointmentListResponse)
def list_appointments(
    status: Optional[AppointmentStatus] = Query(None, description="Durum filtresi"),
    clinic_id: Optional[str] = Query(None, description="Klinik filtresi"),
    email: Optional[str] = Query(None, description="Email filtresi"),
    skip: int = Query(0, ge=0, description="Skip"),
    limit: int = Query(100, ge=1, le=500, description="Limit"),
    db: Session = Depends(get_db)
):
    """
    Randevuları listele (filtreleme ile)
    
    **Filtreler:**
    - status: pending, confirmed, completed, cancelled, no_show
    - clinic_id: Belirli bir klinik
    - email: Belirli bir müşteri
    """
    if email:
        appointments = crud_appointment.get_appointments_by_email(db, email, skip, limit)
    elif clinic_id:
        appointments = crud_appointment.get_appointments_by_clinic(
            db, clinic_id, status.value if status else None, skip, limit
        )
    else:
        appointments = crud_appointment.get_all_appointments(
            db, status.value if status else None, skip, limit
        )
    
    total = crud_appointment.count_appointments(
        db, 
        clinic_id=clinic_id, 
        status=status.value if status else None
    )
    
    return AppointmentListResponse(total=total, appointments=appointments)


@router.get("/clinic/{clinic_id}", response_model=AppointmentListResponse)
def get_clinic_appointments(
    clinic_id: str,
    status: Optional[AppointmentStatus] = Query(None, description="Durum filtresi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Kliniğin randevularını getir
    """
    # Klinik var mı kontrol et
    clinic = get_clinic(db, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    appointments = crud_appointment.get_appointments_by_clinic(
        db, clinic_id, status.value if status else None, skip, limit
    )
    
    total = crud_appointment.count_appointments(db, clinic_id=clinic_id, status=status.value if status else None)
    
    return AppointmentListResponse(total=total, appointments=appointments)


@router.get("/date-range/", response_model=AppointmentListResponse)
def get_appointments_by_date_range(
    start_date: datetime = Query(..., description="Başlangıç tarihi"),
    end_date: datetime = Query(..., description="Bitiş tarihi"),
    clinic_id: Optional[str] = Query(None, description="Klinik filtresi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Tarih aralığına göre randevuları getir
    """
    appointments = crud_appointment.get_appointments_by_date_range(
        db, start_date, end_date, clinic_id, skip, limit
    )
    
    return AppointmentListResponse(total=len(appointments), appointments=appointments)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: str,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Randevu güncelle
    
    **Güncellenebilir Alanlar:**
    - status: pending, confirmed, completed, cancelled, no_show
    - confirmed_date: Onaylanan tarih
    - admin_notes: Admin notları
    - email_sent, sms_sent, reminder_sent: İletişim durumu
    """
    updated_appointment = crud_appointment.update_appointment(db, appointment_id, appointment_update)
    
    if not updated_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return updated_appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: str,
    db: Session = Depends(get_db)
):
    """
    Randevu iptal et
    """
    cancelled_appointment = crud_appointment.cancel_appointment(db, appointment_id)
    
    if not cancelled_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return cancelled_appointment


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db)
):
    """
    Randevu sil (kalıcı)
    """
    success = crud_appointment.delete_appointment(db, appointment_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return None


@router.get("/stats/summary")
def get_appointment_stats(
    clinic_id: Optional[str] = Query(None, description="Klinik filtresi"),
    db: Session = Depends(get_db)
):
    """
    Randevu istatistikleri
    """
    total = crud_appointment.count_appointments(db, clinic_id=clinic_id)
    pending = crud_appointment.count_appointments(db, clinic_id=clinic_id, status="pending")
    confirmed = crud_appointment.count_appointments(db, clinic_id=clinic_id, status="confirmed")
    completed = crud_appointment.count_appointments(db, clinic_id=clinic_id, status="completed")
    cancelled = crud_appointment.count_appointments(db, clinic_id=clinic_id, status="cancelled")
    
    return {
        "total": total,
        "pending": pending,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled
    }
