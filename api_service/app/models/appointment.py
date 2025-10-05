"""
Appointment Model - Randevu Yönetimi
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class Appointment(Base):
    """
    Randevu modeli
    
    Özellikler:
    - Müşteri bilgileri (ad, email, telefon)
    - Klinik seçimi
    - Tedavi seçimi
    - Tarih/saat
    - Durum takibi (pending, confirmed, completed, cancelled)
    - Notlar
    """
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, index=True)
    
    # Müşteri Bilgileri
    customer_name = Column(String, nullable=False, index=True)
    customer_email = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=False)
    customer_country = Column(String, nullable=True)  # Hangi ülkeden geldiği
    customer_language = Column(String, default="tr")  # Tercih ettiği dil
    
    # Randevu Detayları
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    treatment_name = Column(String, nullable=False)  # Hangi tedavi
    preferred_date = Column(DateTime, nullable=False, index=True)  # İstenen tarih
    alternative_date = Column(DateTime, nullable=True)  # Alternatif tarih
    
    # Durum Bilgileri
    status = Column(String, default="pending", index=True)  
    # Status: pending, confirmed, completed, cancelled, no_show
    
    confirmed_date = Column(DateTime, nullable=True)  # Onaylanan tarih
    confirmation_date = Column(DateTime, nullable=True)  # Ne zaman onaylandı
    
    # Ek Bilgiler
    notes = Column(Text, nullable=True)  # Müşterinin notları
    admin_notes = Column(Text, nullable=True)  # Klinik/admin notları
    estimated_price = Column(Integer, nullable=True)  # Tahmini fiyat
    currency = Column(String, default="EUR")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İletişim Durumu
    email_sent = Column(Boolean, default=False)  # Email gönderildi mi
    sms_sent = Column(Boolean, default=False)  # SMS gönderildi mi
    reminder_sent = Column(Boolean, default=False)  # Hatırlatma gönderildi mi
    
    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment {self.id}: {self.customer_name} - {self.clinic_id} - {self.status}>"
    
    def to_dict(self):
        """JSON serialization için"""
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "customer_country": self.customer_country,
            "customer_language": self.customer_language,
            "clinic_id": self.clinic_id,
            "treatment_name": self.treatment_name,
            "preferred_date": self.preferred_date.isoformat() if self.preferred_date else None,
            "alternative_date": self.alternative_date.isoformat() if self.alternative_date else None,
            "status": self.status,
            "confirmed_date": self.confirmed_date.isoformat() if self.confirmed_date else None,
            "confirmation_date": self.confirmation_date.isoformat() if self.confirmation_date else None,
            "notes": self.notes,
            "admin_notes": self.admin_notes,
            "estimated_price": self.estimated_price,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "email_sent": self.email_sent,
            "sms_sent": self.sms_sent,
            "reminder_sent": self.reminder_sent
        }
