#!/usr/bin/env python3
"""
Test script to verify database is working correctly.
Tests SQLAlchemy models and queries.
"""
import sys
from pathlib import Path

# Add api_service to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models import Clinic, Hotel, ChatHistory
from datetime import datetime

def test_database():
    """Test database connection and queries."""
    print("=" * 50)
    print("🧪 Testing Database Connection")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Test 1: Count clinics
        print("\n1️⃣ Testing Clinics Table:")
        clinic_count = db.query(Clinic).count()
        print(f"   ✅ Total clinics: {clinic_count}")
        
        # Test 2: Query clinics by city
        antalya_clinics = db.query(Clinic).filter(Clinic.city == "Antalya").count()
        print(f"   ✅ Antalya clinics: {antalya_clinics}")
        
        # Test 3: Get a clinic with treatments
        sample_clinic = db.query(Clinic).filter(Clinic.id == "ant_clinic_001").first()
        if sample_clinic:
            print(f"   ✅ Sample clinic: {sample_clinic.name}")
            print(f"   ✅ Treatments: {sample_clinic.treatments[:2]}...")
        
        # Test 4: Count hotels
        print("\n2️⃣ Testing Hotels Table:")
        hotel_count = db.query(Hotel).count()
        print(f"   ✅ Total hotels: {hotel_count}")
        
        # Test 5: Get a hotel with features
        sample_hotel = db.query(Hotel).first()
        if sample_hotel:
            print(f"   ✅ Sample hotel: {sample_hotel.name}")
            print(f"   ✅ Features: {sample_hotel.features[:2]}...")
            print(f"   ✅ Amenities: {sample_hotel.amenities[:2]}...")
        
        # Test 6: Test chat history (insert and query)
        print("\n3️⃣ Testing Chat History Table:")
        
        # Insert test chat
        test_chat = ChatHistory(
            session_id="test_session_123",
            user_message="Antalya'da diş kliniği arıyorum",
            bot_response="Size 3 klinik öneririm...",
            intent="search_clinic",
            intent_confidence="0.999",
            entities={"city": "Antalya", "treatment": "dental"},
            language="tr",
            response_time_ms=250
        )
        db.add(test_chat)
        db.commit()
        print("   ✅ Test chat inserted")
        
        # Query chat history
        chat_count = db.query(ChatHistory).count()
        print(f"   ✅ Total chats: {chat_count}")
        
        # Query by session
        session_chats = db.query(ChatHistory).filter(
            ChatHistory.session_id == "test_session_123"
        ).all()
        print(f"   ✅ Chats in test session: {len(session_chats)}")
        
        if session_chats:
            print(f"   ✅ Sample chat: {session_chats[0].user_message}")
            print(f"   ✅ Entities: {session_chats[0].entities}")
        
        # Test 7: Complex query - Clinics with rating > 4.5 in Antalya
        print("\n4️⃣ Testing Complex Queries:")
        high_rated = db.query(Clinic).filter(
            Clinic.city == "Antalya",
            Clinic.rating > 4.5
        ).count()
        print(f"   ✅ High-rated clinics in Antalya (>4.5): {high_rated}")
        
        print("\n" + "=" * 50)
        print("✅ All database tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_database()
