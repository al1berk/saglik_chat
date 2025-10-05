# Chat geçmişi veritabanı modeli (Basitleştirilmiş - User ID yok)
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from app.db.session import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)  # Frontend'den gelen session ID
    
    # Message content
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    
    # NLU results from Rasa
    intent = Column(String(50), index=True)  # search_clinic, search_hotel, etc.
    intent_confidence = Column(String)  # "0.999"
    entities = Column(JSON)  # {"city": "Antalya", "treatment": "dental"}
    
    # Language
    language = Column(String(10), index=True)  # tr, en, de, ar, ru, nl
    
    # Metadata
    response_time_ms = Column(Integer)  # Response time in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

