# Chat endpointi - Rasa ile entegrasyon
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import logging

from app.services.search_service import search_service
from app.core.ollama import ollama_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    sender: str = "user"

class ChatResponse(BaseModel):
    response: str
    sender: str = "bot"

@router.post("/", response_model=list[ChatResponse])
async def chat(message: ChatMessage):
    """
    Kullanıcı mesajını Rasa'ya gönder, ChromaDB'de ara ve Ollama ile yanıt üret
    
    Akış:
    1. Rasa'ya mesaj gönder → Intent ve Entities al
    2. Intent'e göre ChromaDB'de ara
    3. Bulunan sonuçları Ollama'ya gönder → Doğal dil cevabı üret
    4. Yanıtı kullanıcıya döndür
    """
    try:
        # 1. Rasa'ya mesaj gönder
        rasa_url = "http://localhost:5005/webhooks/rest/webhook"
        
        payload = {
            "sender": message.sender,
            "message": message.message
        }
        
        logger.info(f"Rasa'ya mesaj gönderiliyor: {message.message}")
        
        response = requests.post(rasa_url, json=payload, timeout=30)
        response.raise_for_status()
        
        rasa_responses = response.json()
        
        # 2. Rasa'dan gelen yanıtları formatla
        chat_responses = []
        for rasa_response in rasa_responses:
            chat_responses.append(
                ChatResponse(
                    response=rasa_response.get("text", ""),
                    sender="bot"
                )
            )
        
        # Eğer Rasa yanıt vermediyse
        if not chat_responses:
            chat_responses.append(
                ChatResponse(
                    response="Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen tekrar deneyin.",
                    sender="bot"
                )
            )
        
        return chat_responses
        
    except requests.exceptions.ConnectionError:
        logger.error("Rasa servisine bağlanılamadı")
        raise HTTPException(
            status_code=503,
            detail="Rasa servisi çalışmıyor. Lütfen 'rasa run' komutunu çalıştırın."
        )
    except requests.exceptions.Timeout:
        logger.error("Rasa servisi timeout")
        raise HTTPException(
            status_code=504,
            detail="Rasa servisi yanıt vermedi. Lütfen tekrar deneyin."
        )
    except Exception as e:
        logger.error(f"Chat hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bir hata oluştu: {str(e)}"
        )

@router.post("/smart", response_model=ChatResponse)
async def smart_chat(message: ChatMessage):
    """
    Akıllı chat - ChromaDB + Ollama kullanarak doğrudan yanıt ver
    Rasa olmadan da çalışabilir
    """
    try:
        user_message = message.message.lower()
        
        # Basit intent tespiti
        if any(word in user_message for word in ["klinik", "hastane", "doktor", "tedavi", "ameliyat"]):
            # Klinik ara
            clinics = search_service.search_clinics(
                query=message.message,
                limit=5
            )
            
            if clinics:
                response_text = ollama_service.generate_clinic_recommendation(
                    clinics=clinics,
                    user_query=message.message
                )
            else:
                response_text = "Üzgünüm, aradığınız kriterlere uygun klinik bulamadım."
                
        elif any(word in user_message for word in ["otel", "konaklama", "kalacak", "nerede"]):
            # Otel ara
            hotels = search_service.search_hotels(
                query=message.message,
                limit=5
            )
            
            if hotels:
                response_text = ollama_service.generate_hotel_recommendation(
                    hotels=hotels,
                    user_query=message.message
                )
            else:
                response_text = "Üzgünüm, aradığınız kriterlere uygun otel bulamadım."
        else:
            # Genel soru - Ollama'ya sor
            result = ollama_service.generate_response(
                prompt=message.message,
                system_prompt="Sen bir Türk sağlık turizmi asistanısın. Kısa ve yardımcı yanıtlar ver."
            )
            
            if result["success"]:
                response_text = result["response"]
            else:
                response_text = "Üzgünüm, şu anda bu soruya yanıt veremiyorum."
        
        return ChatResponse(
            response=response_text,
            sender="bot"
        )
        
    except Exception as e:
        logger.error(f"Smart chat hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bir hata oluştu: {str(e)}"
        )
