"""
Appointment CRUD Operations
"""
from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from datetime import datetime
import uuid
from typing import Optional, List


def create_appointment(db: Session, appointment: AppointmentCreate) -> Appointment:
    """
    Yeni randevu oluştur
    """
    # Unique ID oluştur
    appointment_id = f"apt_{uuid.uuid4().hex[:12]}"
    
    db_appointment = Appointment(
        id=appointment_id,
        customer_name=appointment.customer_name,
        customer_email=appointment.customer_email,
        customer_phone=appointment.customer_phone,
        customer_country=appointment.customer_country,
        customer_language=appointment.customer_language,
        clinic_id=appointment.clinic_id,
        treatment_name=appointment.treatment_name,
        preferred_date=appointment.preferred_date,
        alternative_date=appointment.alternative_date,
        notes=appointment.notes,
        estimated_price=appointment.estimated_price,
        currency=appointment.currency,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment


def get_appointment(db: Session, appointment_id: str) -> Optional[Appointment]:
    """
    ID'ye göre randevu getir
    """
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments_by_clinic(
    db: Session, 
    clinic_id: str, 
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Appointment]:
    """
    Kliniğe göre randevuları getir
    """
    query = db.query(Appointment).filter(Appointment.clinic_id == clinic_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.order_by(Appointment.preferred_date.desc()).offset(skip).limit(limit).all()


def get_appointments_by_email(
    db: Session, 
    email: str,
    skip: int = 0, 
    limit: int = 100
) -> List[Appointment]:
    """
    Email'e göre müşterinin randevularını getir
    """
    return db.query(Appointment)\
        .filter(Appointment.customer_email == email)\
        .order_by(Appointment.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_appointments_by_date_range(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    clinic_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Appointment]:
    """
    Tarih aralığına göre randevuları getir
    """
    query = db.query(Appointment)\
        .filter(Appointment.preferred_date >= start_date)\
        .filter(Appointment.preferred_date <= end_date)
    
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    
    return query.order_by(Appointment.preferred_date).offset(skip).limit(limit).all()


def get_all_appointments(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Appointment]:
    """
    Tüm randevuları getir
    """
    query = db.query(Appointment)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.order_by(Appointment.created_at.desc()).offset(skip).limit(limit).all()


def update_appointment(
    db: Session, 
    appointment_id: str, 
    appointment_update: AppointmentUpdate
) -> Optional[Appointment]:
    """
    Randevu güncelle
    """
    db_appointment = get_appointment(db, appointment_id)
    
    if not db_appointment:
        return None
    
    update_data = appointment_update.model_dump(exclude_unset=True)
    
    # Eğer status confirmed'a alınıyorsa, confirmation_date ekle
    if update_data.get("status") == "confirmed" and db_appointment.status != "confirmed":
        update_data["confirmation_date"] = datetime.utcnow()
    
    # Alanları güncelle
    for field, value in update_data.items():
        setattr(db_appointment, field, value)
    
    db_appointment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment


def cancel_appointment(db: Session, appointment_id: str) -> Optional[Appointment]:
    """
    Randevu iptal et
    """
    db_appointment = get_appointment(db, appointment_id)
    
    if not db_appointment:
        return None
    
    db_appointment.status = "cancelled"
    db_appointment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment


def delete_appointment(db: Session, appointment_id: str) -> bool:
    """
    Randevu sil (kalıcı)
    """
    db_appointment = get_appointment(db, appointment_id)
    
    if not db_appointment:
        return False
    
    db.delete(db_appointment)
    db.commit()
    
    return True


def count_appointments(
    db: Session,
    clinic_id: Optional[str] = None,
    status: Optional[str] = None
) -> int:
    """
    Randevu sayısını getir
    """
    query = db.query(Appointment)
    
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    return query.count()
