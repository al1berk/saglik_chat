"""
Ollama LLM Servisi
Yerel olarak çalışan Ollama ile etkileşim için servis
"""
import requests
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """Ollama API ile etkileşim için servis sınıfı"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
    
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ollama'dan yanıt üret
        
        Args:
            prompt: Kullanıcı sorusu
            system_prompt: Sistem promptu (opsiyonel)
            context: Ek bağlam bilgisi (opsiyonel)
            
        Returns:
            Dict: Ollama yanıtı ve metadata
        """
        try:
            # Prompt'u hazırla
            full_prompt = self._build_prompt(prompt, system_prompt, context)
            
            # Ollama API'ye istek gönder
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                }
            }
            
            logger.info(f"Ollama'ya istek gönderiliyor: {self.model}")
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=60,
                proxies={"http": None, "https": None}
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "response": result.get("response", "").strip(),
                "model": result.get("model"),
                "done": result.get("done", True)
            }
            
        except requests.exceptions.ConnectionError:
            logger.error("Ollama servisine bağlanılamadı")
            return {
                "success": False,
                "error": "Ollama servisi çalışmıyor. 'ollama serve' komutunu çalıştırın."
            }
        except requests.exceptions.Timeout:
            logger.error("Ollama servisi zaman aşımı")
            return {
                "success": False,
                "error": "Ollama yanıt vermedi. Lütfen tekrar deneyin."
            }
        except Exception as e:
            logger.error(f"Ollama hatası: {e}")
            return {
                "success": False,
                "error": f"Beklenmeyen hata: {str(e)}"
            }
    
    def _build_prompt(
        self, 
        prompt: str, 
        system_prompt: Optional[str], 
        context: Optional[str]
    ) -> str:
        """Tam prompt'u oluştur"""
        parts = []
        
        # Sistem promptu
        if system_prompt:
            parts.append(f"[SİSTEM]: {system_prompt}")
        else:
            parts.append("[SİSTEM]: Sen bir Türk sağlık turizmi asistanısın. Türkiye'deki klinikleri, otelleri ve tedavileri hakkında bilgi veriyorsun. Her zaman Türkçe konuş.")
        
        # Bağlam bilgisi
        if context:
            parts.append(f"\n[BAĞLAM]:\n{context}")
        
        # Kullanıcı sorusu
        parts.append(f"\n[KULLANICI]: {prompt}")
        parts.append("\n[ASİSTAN]:")
        
        return "\n".join(parts)
    
    def generate_clinic_recommendation(
        self, 
        clinics: list, 
        user_query: str
    ) -> str:
        """
        Klinik listesi için öneri üret
        
        Args:
            clinics: Klinik listesi
            user_query: Kullanıcı sorusu
            
        Returns:
            str: Doğal dil ile öneri metni
        """
        if not clinics:
            return "Üzgünüm, aradığınız kriterlere uygun klinik bulamadım."
        
        # Klinik bilgilerini context olarak hazırla
        context = "BULUNAN KLİNİKLER:\n"
        for i, clinic in enumerate(clinics[:5], 1):
            context += f"{i}. {clinic.get('name', 'İsimsiz Klinik')}\n"
            context += f"   Şehir: {clinic.get('city', 'Belirtilmemiş')}\n"
            context += f"   Puan: {clinic.get('rating', 'N/A')}\n"
            context += f"   Telefon: {clinic.get('phone', 'Belirtilmemiş')}\n"
            
            treatments = clinic.get('treatments', [])
            if treatments:
                context += f"   Tedaviler: {', '.join(treatments[:3])}\n"
            context += "\n"
        
        system_prompt = "Sen bir sağlık turizmi danışmanısın. Verilen klinik bilgilerini kullanarak kullanıcıya yardımcı ol. Kısa ve öz açıklamalar yap. Yanıtın tamamen Türkçe olsun."
        
        prompt = f"Kullanıcı şunu sordu: '{user_query}'\n\nYukarıdaki klinikleri kısaca öner ve hangisinin neden uygun olabileceğini belirt."
        
        result = self.generate_response(prompt, system_prompt, context)
        
        if result["success"]:
            return result["response"]
        else:
            # Hata durumunda basit bir yanıt döndür
            simple_response = f"🏥 Sizin için {len(clinics)} klinik buldum:\n\n"
            for i, clinic in enumerate(clinics[:3], 1):
                simple_response += f"{i}. **{clinic.get('name')}** - {clinic.get('city')}\n"
                simple_response += f"   ⭐ Puan: {clinic.get('rating')}\n\n"
            return simple_response
    
    def generate_hotel_recommendation(
        self, 
        hotels: list, 
        user_query: str
    ) -> str:
        """
        Otel listesi için öneri üret
        
        Args:
            hotels: Otel listesi
            user_query: Kullanıcı sorusu
            
        Returns:
            str: Doğal dil ile öneri metni
        """
        if not hotels:
            return "Üzgünüm, aradığınız kriterlere uygun otel bulamadım."
        
        # Otel bilgilerini context olarak hazırla
        context = "BULUNAN OTELLER:\n"
        for i, hotel in enumerate(hotels[:5], 1):
            context += f"{i}. {hotel.get('name', 'İsimsiz Otel')}\n"
            context += f"   Şehir: {hotel.get('city', 'Belirtilmemiş')}\n"
            context += f"   Puan: {hotel.get('rating', 'N/A')}\n"
            context += f"   Gecelik Fiyat: ${hotel.get('price_per_night', 'N/A')}\n"
            
            features = hotel.get('features', [])
            if features:
                context += f"   Özellikler: {', '.join(features[:3])}\n"
            context += "\n"
        
        system_prompt = "Sen bir sağlık turizmi danışmanısın. Verilen otel bilgilerini kullanarak kullanıcıya yardımcı ol. Kısa ve öz açıklamalar yap. Yanıtın tamamen Türkçe olsun."
        
        prompt = f"Kullanıcı şunu sordu: '{user_query}'\n\nYukarıdaki otelleri kısaca öner ve hangisinin neden uygun olabileceğini belirt."
        
        result = self.generate_response(prompt, system_prompt, context)
        
        if result["success"]:
            return result["response"]
        else:
            # Hata durumunda basit bir yanıt döndür
            simple_response = f"🏨 Sizin için {len(hotels)} otel buldum:\n\n"
            for i, hotel in enumerate(hotels[:3], 1):
                simple_response += f"{i}. **{hotel.get('name')}** - {hotel.get('city')}\n"
                simple_response += f"   ⭐ Puan: {hotel.get('rating')}, Gecelik: ${hotel.get('price_per_night')}\n\n"
            return simple_response

# Global instance
ollama_service = OllamaService()
