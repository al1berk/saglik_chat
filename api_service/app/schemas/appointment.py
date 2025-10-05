"""
Appointment Schemas - Pydantic modelleri
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    """Randevu durumları"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentCreate(BaseModel):
    """Yeni randevu oluşturma"""
    # Müşteri Bilgileri (ZORUNLU)
    customer_name: str = Field(..., min_length=2, max_length=100, description="Müşteri adı soyadı")
    customer_email: EmailStr = Field(..., description="Email adresi")
    customer_phone: str = Field(..., min_length=10, max_length=20, description="Telefon numarası")
    customer_country: Optional[str] = Field(None, max_length=50, description="Ülke")
    customer_language: str = Field("tr", description="Dil tercihi (tr, en, de, ar, ru, nl)")
    
    # Randevu Detayları (ZORUNLU)
    clinic_id: str = Field(..., description="Klinik ID'si")
    treatment_name: str = Field(..., description="Tedavi adı")
    preferred_date: datetime = Field(..., description="İstenen randevu tarihi (ISO format)")
    alternative_date: Optional[datetime] = Field(None, description="Alternatif tarih")
    
    # Ek Bilgiler (OPSİYONEL)
    notes: Optional[str] = Field(None, max_length=1000, description="Müşteri notları")
    estimated_price: Optional[int] = Field(None, ge=0, description="Tahmini fiyat")
    currency: str = Field("EUR", description="Para birimi")

    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "Mehmet Yılmaz",
                "customer_email": "mehmet@example.com",
                "customer_phone": "+90 532 123 45 67",
                "customer_country": "Germany",
                "customer_language": "de",
                "clinic_id": "ant_clinic_001",
                "treatment_name": "Composite Bonding",
                "preferred_date": "2025-10-15T10:00:00",
                "alternative_date": "2025-10-16T14:00:00",
                "notes": "Dişlerimin rengini düzeltmek istiyorum",
                "estimated_price": 250,
                "currency": "EUR"
            }
        }


class AppointmentUpdate(BaseModel):
    """Randevu güncelleme"""
    status: Optional[AppointmentStatus] = None
    confirmed_date: Optional[datetime] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)
    email_sent: Optional[bool] = None
    sms_sent: Optional[bool] = None
    reminder_sent: Optional[bool] = None


class AppointmentResponse(BaseModel):
    """Randevu yanıtı"""
    id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_country: Optional[str]
    customer_language: str
    clinic_id: str
    treatment_name: str
    preferred_date: datetime
    alternative_date: Optional[datetime]
    status: str
    confirmed_date: Optional[datetime]
    confirmation_date: Optional[datetime]
    notes: Optional[str]
    admin_notes: Optional[str]
    estimated_price: Optional[int]
    currency: str
    created_at: datetime
    updated_at: datetime
    email_sent: bool
    sms_sent: bool
    reminder_sent: bool

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Randevu listesi yanıtı"""
    total: int
    appointments: list[AppointmentResponse]
