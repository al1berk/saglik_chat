"""
Appointments Tablosu Migration Script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, SessionLocal
from app.models.clinic import Clinic
from app.models.hotel import Hotel
from app.models.appointment import Appointment  # YENİ!
from sqlalchemy import inspect

def create_appointments_table():
    """
    Appointments tablosunu oluştur
    """
    print("🔧 Appointments tablosu oluşturuluyor...")
    
    # Tabloları oluştur
    Appointment.__table__.create(bind=engine, checkfirst=True)
    
    print("✅ Appointments tablosu başarıyla oluşturuldu!")
    
    # Tablo bilgilerini göster
    inspector = inspect(engine)
    if inspector.has_table("appointments"):
        columns = inspector.get_columns("appointments")
        print(f"\n📊 Appointments tablosu sütunları ({len(columns)} adet):")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
    
    return True


def test_appointment_creation():
    """
    Test randevusu oluştur
    """
    print("\n🧪 Test randevusu oluşturuluyor...")
    
    db = SessionLocal()
    
    try:
        # İlk kliniği bul
        first_clinic = db.query(Clinic).first()
        
        if not first_clinic:
            print("⚠️  Veritabanında klinik bulunamadı. Önce seed_database.py çalıştırın.")
            return False
        
        # Test randevusu
        from datetime import datetime, timedelta
        import uuid
        
        test_appointment = Appointment(
            id=f"apt_{uuid.uuid4().hex[:12]}",
            customer_name="Test Müşteri",
            customer_email="test@example.com",
            customer_phone="+90 532 123 45 67",
            customer_country="Germany",
            customer_language="de",
            clinic_id=first_clinic.id,
            treatment_name="Composite Bonding",
            preferred_date=datetime.now() + timedelta(days=7),
            status="pending",
            notes="Bu bir test randevusudur",
            estimated_price=250,
            currency="EUR",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(test_appointment)
        db.commit()
        db.refresh(test_appointment)
        
        print(f"✅ Test randevusu oluşturuldu:")
        print(f"   ID: {test_appointment.id}")
        print(f"   Müşteri: {test_appointment.customer_name}")
        print(f"   Klinik: {first_clinic.name}")
        print(f"   Tedavi: {test_appointment.treatment_name}")
        print(f"   Tarih: {test_appointment.preferred_date}")
        print(f"   Durum: {test_appointment.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    print("=" * 70)
    print("📅 APPOINTMENTS TABLOSU MIGRATION")
    print("=" * 70)
    
    # 1. Tabloyu oluştur
    if not create_appointments_table():
        print("\n❌ Migration başarısız!")
        return
    
    # 2. Test randevusu oluştur
    if not test_appointment_creation():
        print("\n⚠️  Test randevusu oluşturulamadı (normal, klinik yoksa)")
    
    print("\n" + "=" * 70)
    print("🎉 MIGRATION TAMAMLANDI!")
    print("=" * 70)
    print("\n✅ Artık randevu sistemi kullanıma hazır!")
    print("\n📝 API Endpoints:")
    print("   POST   /api/appointments          - Yeni randevu")
    print("   GET    /api/appointments/{id}     - Randevu detay")
    print("   GET    /api/appointments          - Tüm randevular")
    print("   GET    /api/appointments/clinic/{id} - Klinik randevuları")
    print("   PATCH  /api/appointments/{id}     - Randevu güncelle")
    print("   POST   /api/appointments/{id}/cancel - İptal et")
    print("   DELETE /api/appointments/{id}     - Sil")
    print("   GET    /api/appointments/stats/summary - İstatistikler")


if __name__ == "__main__":
    main()
