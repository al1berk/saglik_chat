# Database initialization
"""
Initialize database tables and seed with initial data.
This script creates all tables and optionally loads data from JSON files.
"""
from sqlalchemy.orm import Session
from app.db.session import engine, Base, SessionLocal
from app.models import Clinic, Hotel, ChatHistory
import json
from pathlib import Path
from datetime import datetime

def init_db() -> None:
    """
    Create all database tables.
    This uses SQLAlchemy's create_all which is idempotent.
    """
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def load_clinics_from_json(db: Session) -> int:
    """
    Load clinic data from JSON file into database.
    Returns the number of clinics loaded.
    """
    json_path = Path(__file__).parent.parent.parent / "data" / "raw" / "clinics.json"
    
    if not json_path.exists():
        print(f"⚠️  Clinic JSON file not found: {json_path}")
        return 0
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    clinics_data = data.get("all_clinics", [])
    count = 0
    
    for clinic_data in clinics_data:
        # Check if clinic already exists
        existing = db.query(Clinic).filter(Clinic.id == clinic_data["id"]).first()
        if existing:
            continue
        
        clinic = Clinic(
            id=clinic_data["id"],
            name=clinic_data["name"],
            city=clinic_data.get("city", "Unknown"),
            country="Turkey",
            address=clinic_data.get("address", ""),
            rating=clinic_data.get("rating", 0.0),
            phone=clinic_data.get("phone", ""),
            treatments=clinic_data.get("treatments", []),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(clinic)
        count += 1
    
    db.commit()
    return count


def load_hotels_from_json(db: Session) -> int:
    """
    Load hotel data from JSON file into database.
    Returns the number of hotels loaded.
    """
    json_path = Path(__file__).parent.parent.parent / "data" / "raw" / "hotels.json"
    
    if not json_path.exists():
        print(f"⚠️  Hotel JSON file not found: {json_path}")
        return 0
    
    with open(json_path, "r", encoding="utf-8") as f:
        hotels_data = json.load(f)
    
    # hotels.json is an array, not an object with "all_hotels" key
    if not isinstance(hotels_data, list):
        hotels_data = hotels_data.get("all_hotels", [])
    
    count = 0
    
    for hotel_data in hotels_data:
        # Check if hotel already exists
        existing = db.query(Hotel).filter(Hotel.id == hotel_data["id"]).first()
        if existing:
            continue
        
        # Extract phone from contact if it exists
        phone = ""
        if "contact" in hotel_data and isinstance(hotel_data["contact"], dict):
            phone = hotel_data["contact"].get("phone", "")
        else:
            phone = hotel_data.get("phone", "")
        
        hotel = Hotel(
            id=hotel_data["id"],
            name=hotel_data["name"],
            city=hotel_data.get("city", "Unknown"),
            country=hotel_data.get("country", "Turkey"),
            address=hotel_data.get("address", ""),
            rating=hotel_data.get("rating", 0.0),
            price_per_night=hotel_data.get("price_per_night", 0.0),
            phone=phone,
            features=hotel_data.get("features", []),
            amenities=hotel_data.get("amenities", []),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(hotel)
        count += 1
    
    db.commit()
    return count


def seed_database() -> None:
    """
    Seed the database with initial data from JSON files.
    """
    print("🌱 Seeding database with initial data...")
    db = SessionLocal()
    
    try:
        # Load clinics
        clinics_count = load_clinics_from_json(db)
        print(f"✅ Loaded {clinics_count} clinics")
        
        # Load hotels
        hotels_count = load_hotels_from_json(db)
        print(f"✅ Loaded {hotels_count} hotels")
        
        print("🎉 Database seeding completed!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Database Initialization")
    print("=" * 50)
    
    # Create tables
    init_db()
    
    # Seed with data
    seed_database()
    
    print("\n✨ All done! Database is ready.")
