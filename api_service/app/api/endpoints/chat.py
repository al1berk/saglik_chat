# Chat endpointi - Rasa ile entegrasyon
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import logging

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
    Kullanıcı mesajını Rasa'ya gönder ve yanıtı al
    """
    try:
        # Rasa'ya mesaj gönder
        rasa_url = "http://localhost:5005/webhooks/rest/webhook"
        
        payload = {
            "sender": message.sender,
            "message": message.message
        }
        
        logger.info(f"Rasa'ya mesaj gönderiliyor: {message.message}")
        
        response = requests.post(rasa_url, json=payload, timeout=30)
        response.raise_for_status()
        
        rasa_responses = response.json()
        
        # Rasa'dan gelen yanıtları formatla
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
