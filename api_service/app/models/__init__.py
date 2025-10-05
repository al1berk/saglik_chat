# Models module - Database models (Simplified)
from app.models.clinic import Clinic
from app.models.hotel import Hotel
from app.models.chat_history import ChatHistory
from app.models.appointment import Appointment

__all__ = ["Clinic", "Hotel", "ChatHistory", "Appointment"]

