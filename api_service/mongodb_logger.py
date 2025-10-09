# backend/mongodb_logger.py
"""
MongoDB Logger for Health Tourism Chatbot
Hocanızın istediği JSON yapısında user profili ve conversation loglarını saklar
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBLogger:
    """
    MongoDB'ye sağlık turizmi chatbot verilerini kaydeder
    
    Collections:
    - users: User profilleri
    - conversations: Mesaj logları
    - bookings: Randevu/rezervasyon kayıtları
    """
    
    def __init__(self, 
                 uri: str = "mongodb://localhost:27017/",
                 database: str = "health_tourism"):
        """
        MongoDB bağlantısını başlat
        
        Args:
            uri: MongoDB connection string
            database: Database adı
        """
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Bağlantıyı test et
            self.client.admin.command('ping')
            logger.info("✅ MongoDB bağlantısı başarılı")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB'ye bağlanılamadı: {e}")
            raise
        
        # Database ve collections
        self.db = self.client[database]
        self.users = self.db["users"]
        self.conversations = self.db["conversations"]
        self.bookings = self.db["bookings"]
        
        # Index'leri oluştur
        self._create_indexes()
    
    def _create_indexes(self):
        """Performans için index'ler oluştur"""
        try:
            # Users collection indexes
            self.users.create_index("user_id", unique=True)
            self.users.create_index("created_at")
            
            # Conversations collection indexes
            self.conversations.create_index([
                ("user_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            self.conversations.create_index("intent")
            self.conversations.create_index("timestamp")
            
            # Bookings collection indexes
            self.bookings.create_index("user_id")
            self.bookings.create_index("status")
            self.bookings.create_index("appointment_date")
            
            logger.info("✅ MongoDB indexes oluşturuldu")
        except Exception as e:
            logger.warning(f"⚠️ Index oluşturma hatası: {e}")
    
    # ============================================
    # USER PROFILE OPERATIONS
    # ============================================
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Yeni user profili oluştur
        
        Args:
            user_data: {
                "user_id": "telegram_123456",  # ZORUNLU
                "name": "Ahmet Yılmaz",
                "age": 35,
                "gender": "male",
                "email": "ahmet@example.com",
                "phone": "+905551234567",
                "country": "Turkey",
                "health_conditions": ["diabetes", "hypertension"],
                "preferences": {
                    "treatment": "dental implant",
                    "city": "Antalya",
                    "budget": 5000,
                    "language": "tr"
                }
            }
        
        Returns:
            user_id: Oluşturulan user'ın ID'si
        """
        if "user_id" not in user_data:
            raise ValueError("user_id zorunludur!")
        
        user_id = user_data["user_id"]
        
        # Timestamp ekle
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        try:
            self.users.insert_one(user_data)
            logger.info(f"✅ User oluşturuldu: {user_id}")
            return user_id
        
        except DuplicateKeyError:
            logger.warning(f"⚠️ User zaten mevcut: {user_id}")
            return user_id
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        User profilini güncelle
        
        Args:
            user_id: User ID
            updates: Güncellenecek alanlar
        
        Returns:
            bool: Başarılı ise True
        """
        updates["updated_at"] = datetime.utcnow()
        
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ User güncellendi: {user_id}")
            return True
        else:
            logger.warning(f"⚠️ User bulunamadı: {user_id}")
            return False
    
    def upsert_user(self, user_data: Dict[str, Any]) -> str:
        """
        User var ise güncelle, yoksa oluştur (Upsert)
        
        Args:
            user_data: User bilgileri
        
        Returns:
            user_id
        """
        if "user_id" not in user_data:
            raise ValueError("user_id zorunludur!")
        
        user_id = user_data["user_id"]
        
        # Timestamp'leri ayarla
        user_data["updated_at"] = datetime.utcnow()
        
        # Eğer user yoksa created_at ekle
        existing_user = self.users.find_one({"user_id": user_id})
        if not existing_user:
            user_data["created_at"] = datetime.utcnow()
        
        # Upsert
        self.users.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
        
        logger.info(f"✅ User upsert: {user_id}")
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """User profilini getir"""
        user = self.users.find_one({"user_id": user_id}, {"_id": 0})
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """User'ı sil (GDPR için)"""
        result = self.users.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
            logger.info(f"🗑️ User silindi: {user_id}")
            return True
        return False
    
    # ============================================
    # CONVERSATION LOGGING
    # ============================================
    
    def log_message(self, 
                    user_id: str,
                    sender: str,  # "user" veya "bot"
                    text: str,
                    intent: Optional[str] = None,
                    entities: Optional[List[Dict]] = None,
                    confidence: Optional[float] = None,
                    bot_action: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> str:
        """
        Tek bir mesajı kaydet
        
        Args:
            user_id: User ID
            sender: "user" veya "bot"
            text: Mesaj metni
            intent: Algılanan intent (sadece user mesajları için)
            entities: Çıkarılan entity'ler
            confidence: Intent confidence skoru
            bot_action: Bot'un çalıştırdığı action
            metadata: Ekstra bilgiler
        
        Returns:
            message_id: Kaydedilen mesajın ID'si
        """
        message_data = {
            "user_id": user_id,
            "sender": sender,
            "text": text,
            "timestamp": datetime.utcnow()
        }
        
        # Opsiyonel alanlar
        if intent:
            message_data["intent"] = intent
        if entities:
            message_data["entities"] = entities
        if confidence is not None:
            message_data["confidence"] = confidence
        if bot_action:
            message_data["bot_action"] = bot_action
        if metadata:
            message_data["metadata"] = metadata
        
        result = self.conversations.insert_one(message_data)
        message_id = str(result.inserted_id)
        
        logger.info(f"💬 Mesaj kaydedildi: {user_id} [{sender}]")
        return message_id
    
    def log_conversation_turn(self,
                             user_id: str,
                             user_message: str,
                             user_intent: str,
                             user_entities: List[Dict],
                             bot_response: str,
                             bot_action: str,
                             confidence: float) -> List[str]:
        """
        Bir conversation turn'ünü kaydet (user mesajı + bot cevabı)
        
        Returns:
            List[message_id, message_id]: İki mesajın ID'leri
        """
        # User mesajı
        user_msg_id = self.log_message(
            user_id=user_id,
            sender="user",
            text=user_message,
            intent=user_intent,
            entities=user_entities,
            confidence=confidence
        )
        
        # Bot cevabı
        bot_msg_id = self.log_message(
            user_id=user_id,
            sender="bot",
            text=bot_response,
            bot_action=bot_action
        )
        
        return [user_msg_id, bot_msg_id]
    
    def get_user_conversations(self, 
                              user_id: str,
                              limit: int = 50) -> List[Dict]:
        """
        User'ın son N mesajını getir
        
        Args:
            user_id: User ID
            limit: Kaç mesaj getirileceği
        
        Returns:
            List of messages
        """
        conversations = list(
            self.conversations
            .find({"user_id": user_id}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        
        return conversations
    
    def get_conversation_history(self,
                                user_id: str,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Belirli tarih aralığındaki conversation'ları getir
        """
        query = {"user_id": user_id}
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        conversations = list(
            self.conversations
            .find(query, {"_id": 0})
            .sort("timestamp", ASCENDING)
        )
        
        return conversations
    
    # ============================================
    # BOOKING OPERATIONS
    # ============================================
    
    def create_booking(self, booking_data: Dict[str, Any]) -> str:
        """
        Yeni booking kaydı oluştur
        
        Args:
            booking_data: {
                "user_id": "telegram_123",
                "clinic_name": "Antmodern Clinic",
                "clinic_id": 1,
                "treatment": "dental implant",
                "hotel_name": "Delphin Palace",
                "hotel_id": 1,
                "appointment_date": "2025-11-15",
                "nights": 7,
                "costs": {
                    "treatment": 2000,
                    "hotel": 1400,
                    "flight": 600,
                    "transfer": 150,
                    "total": 4150
                },
                "currency": "EUR",
                "status": "pending",  # pending, confirmed, completed, cancelled
                "notes": "Extra bilgiler"
            }
        
        Returns:
            booking_id
        """
        if "user_id" not in booking_data:
            raise ValueError("user_id zorunludur!")
        
        # Timestamps
        booking_data["created_at"] = datetime.utcnow()
        booking_data["updated_at"] = datetime.utcnow()
        
        # Status default
        if "status" not in booking_data:
            booking_data["status"] = "pending"
        
        result = self.bookings.insert_one(booking_data)
        booking_id = str(result.inserted_id)
        
        logger.info(f"📅 Booking oluşturuldu: {booking_id}")
        return booking_id
    
    def update_booking_status(self, 
                            booking_id: str,
                            new_status: str) -> bool:
        """
        Booking durumunu güncelle
        
        Args:
            booking_id: MongoDB ObjectId (string)
            new_status: pending, confirmed, completed, cancelled
        """
        from bson.objectid import ObjectId
        
        result = self.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def get_user_bookings(self, user_id: str) -> List[Dict]:
        """User'ın tüm booking'lerini getir"""
        bookings = list(
            self.bookings
            .find({"user_id": user_id}, {"_id": 0})
            .sort("created_at", DESCENDING)
        )
        return bookings
    
    # ============================================
    # ANALYTICS & REPORTING
    # ============================================
    
    def get_intent_statistics(self, days: int = 30) -> Dict[str, int]:
        """
        Son N gün içindeki intent dağılımı
        
        Returns:
            {"tedavi_arama_dental": 45, "greet": 120, ...}
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {
                "intent": {"$exists": True, "$ne": None},
                "timestamp": {"$gte": cutoff_date}
            }},
            {"$group": {
                "_id": "$intent",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(self.conversations.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in results}
    
    def get_active_users(self, days: int = 7) -> int:
        """Son N gün içinde aktif olan user sayısı"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        active_users = self.conversations.distinct(
            "user_id",
            {"timestamp": {"$gte": cutoff_date}}
        )
        
        return len(active_users)
    
    def get_total_conversations(self) -> int:
        """Toplam mesaj sayısı"""
        return self.conversations.count_documents({})
    
    def get_booking_stats(self) -> Dict[str, int]:
        """Booking istatistikleri"""
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(self.bookings.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in results}
    
    def get_popular_treatments(self, limit: int = 10) -> List[Dict]:
        """En popüler tedaviler"""
        pipeline = [
            {"$match": {"treatment": {"$exists": True}}},
            {"$group": {
                "_id": "$treatment",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = list(self.bookings.aggregate(pipeline))
        return [{"treatment": item["_id"], "count": item["count"]} for item in results]
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def health_check(self) -> bool:
        """MongoDB bağlantısını kontrol et"""
        try:
            self.client.admin.command('ping')
            return True
        except:
            return False
    
    def clear_old_conversations(self, days: int = 90):
        """90 günden eski conversation'ları sil (GDPR)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = self.conversations.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        logger.info(f"🗑️ {result.deleted_count} eski conversation silindi")
        return result.deleted_count
    
    def close(self):
        """MongoDB bağlantısını kapat"""
        self.client.close()
        logger.info("🔌 MongoDB bağlantısı kapatıldı")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()


# ============================================
# TEST KODU
# ============================================
if __name__ == "__main__":
    print("🧪 MongoDB Logger Test Başlıyor...\n")
    
    # Logger oluştur
    logger_instance = MongoDBLogger()
    
    # Test 1: User oluştur
    print("1️⃣ User Profili Oluşturma")
    user_data = {
        "user_id": "test_user_001",
        "name": "Ahmet Test",
        "age": 35,
        "gender": "male",
        "email": "ahmet@test.com",
        "health_conditions": ["diabetes"],
        "preferences": {
            "treatment": "dental implant",
            "city": "Antalya",
            "budget": 5000
        }
    }
    logger_instance.upsert_user(user_data)
    print(f"   User oluşturuldu: {user_data['user_id']}\n")
    
    # Test 2: Conversation log
    print("2️⃣ Conversation Loglama")
    logger_instance.log_conversation_turn(
        user_id="test_user_001",
        user_message="Antalya'da diş implantı yaptırmak istiyorum",
        user_intent="tedavi_arama_dental",
        user_entities=[
            {"entity": "sehir", "value": "Antalya"},
            {"entity": "tedavi_adi", "value": "dental implant"}
        ],
        bot_response="Harika! Antalya'da 7 dental klinik bulundu.",
        bot_action="utter_antalya_klinikler_dental",
        confidence=0.95
    )
    print("   Conversation kaydedildi\n")
    
    # Test 3: Booking oluştur
    print("3️⃣ Booking Oluşturma")
    booking_data = {
        "user_id": "test_user_001",
        "clinic_name": "Antmodern Clinic",
        "treatment": "dental implant",
        "hotel_name": "Delphin Palace",
        "appointment_date": "2025-11-15",
        "nights": 7,
        "costs": {
            "treatment": 2000,
            "hotel": 1400,
            "flight": 600,
            "transfer": 150,
            "total": 4150
        },
        "currency": "EUR",
        "status": "confirmed"
    }
    booking_id = logger_instance.create_booking(booking_data)
    print(f"   Booking ID: {booking_id}\n")
    
    # Test 4: Analytics
    print("4️⃣ Analytics")
    print(f"   Intent İstatistikleri: {logger_instance.get_intent_statistics()}")
    print(f"   Aktif User Sayısı: {logger_instance.get_active_users(7)}")
    print(f"   Toplam Mesaj: {logger_instance.get_total_conversations()}")
    print(f"   Booking Stats: {logger_instance.get_booking_stats()}\n")
    
    # Test 5: User verilerini getir
    print("5️⃣ User Verilerini Getirme")
    user = logger_instance.get_user("test_user_001")
    print(f"   User: {user['name']}, {user['age']} yaşında")
    
    conversations = logger_instance.get_user_conversations("test_user_001", limit=5)
    print(f"   Son {len(conversations)} mesaj getirildi\n")
    
    # Bağlantıyı kapat
    logger_instance.close()
    
    print("✅ Tüm testler başarılı!")