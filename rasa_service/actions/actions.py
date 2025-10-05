# actions/actions.py

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests
import logging

# Loglama ayarlarını yapılandır
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- API Adresleri ve Sabitler ---
# Kendi yazdığınız FastAPI/Uvicorn servisinizin adresi
API_SERVICE_URL = "http://localhost:8000/api"
# Yerel Ollama sunucunuzun adresi
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Sistemdeki olası proxy ayarlarını devre dışı bırakmak için
# Her istekte bu parametreyi kullanacağız.
PROXIES = {
    "http": None,
    "https": None,
}

class ActionKlinikAra(Action):
    def name(self) -> Text:
        return "action_klinik_ara"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tedavi = next(tracker.get_latest_entity_values("tedavi"), None)
        sehir = next(tracker.get_latest_entity_values("sehir"), None)
        
        logger.info(f"Klinik arama başlatıldı: tedavi={tedavi}, sehir={sehir}")
        
        try:
            api_url = f"{API_SERVICE_URL}/search/clinics"
            params = {"treatment": tedavi, "city": sehir}
            # Yalnızca dolu olan parametreleri gönder
            params = {k: v for k, v in params.items() if v is not None}
                
            response = requests.get(api_url, params=params, timeout=15, proxies=PROXIES)
            response.raise_for_status() # Hatalı status kodları için exception fırlat
            
            clinics = response.json()
            if clinics:
                message = f"🏥 Sizin için {len(clinics)} klinik buldum:\n\n"
                for i, clinic in enumerate(clinics[:3], 1): # İlk 3 sonucu göster
                    message += f"{i}. **{clinic.get('name', 'İsimsiz Klinik')}**\n"
                    message += f"   📍 {clinic.get('city', 'Şehir Belirtilmemiş')}\n"
                    message += f"   ⭐ Puan: {clinic.get('rating', 'N/A')}\n\n"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Üzgünüm, aradığınız kriterlere uygun klinik bulamadım.")
                
        except requests.exceptions.Timeout:
            logger.error("API servisi (klinik arama) zaman aşımına uğradı.")
            dispatcher.utter_message(text="Klinik arama servisi çok yavaş yanıt veriyor. Lütfen sonra deneyin.")
        except requests.exceptions.RequestException as e:
            logger.error(f"API servisi (klinik arama) hatası: {e}")
            dispatcher.utter_message(text="Klinik arama servisine şu anda ulaşılamıyor.")
        
        return []

class ActionOtelAra(Action):
    def name(self) -> Text:
        return "action_otel_ara"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sehir = next(tracker.get_latest_entity_values("sehir"), None)
        otel_tipi = next(tracker.get_latest_entity_values("otel_tipi"), None)
        
        logger.info(f"Otel arama başlatıldı: sehir={sehir}, tip={otel_tipi}")
        
        try:
            api_url = f"{API_SERVICE_URL}/search/hotels"
            params = {"city": sehir, "hotel_type": otel_tipi}
            params = {k: v for k, v in params.items() if v is not None}
                
            response = requests.get(api_url, params=params, timeout=15, proxies=PROXIES)
            response.raise_for_status()
            
            hotels = response.json()
            if hotels:
                message = f"🏨 Sizin için {len(hotels)} otel buldum:\n\n"
                for hotel in hotels[:3]: # İlk 3 sonucu göster
                    message += f"• **{hotel.get('name', 'İsimsiz Otel')}** - {hotel.get('city', '')}\n"
                    message += f"  Puan: {hotel.get('rating', 'N/A')}, Gecelik: ${hotel.get('price_per_night', 'N/A')}\n\n"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Aradığınız kriterlere uygun otel bulamadım.")
                
        except requests.exceptions.Timeout:
            logger.error("API servisi (otel arama) zaman aşımına uğradı.")
            dispatcher.utter_message(text="Otel arama servisi çok yavaş yanıt veriyor. Lütfen sonra deneyin.")
        except requests.exceptions.RequestException as e:
            logger.error(f"API servisi (otel arama) hatası: {e}")
            dispatcher.utter_message(text="Otel arama servisine şu anda ulaşılamıyor.")
        
        return []

class ActionSacEkimiDetaylari(Action):
    def name(self) -> Text:
        return "action_sac_ekimi_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("Saç ekimi bilgisi için Ollama'ya sorgu gönderiliyor...")

        # --- GÜNCELLENMİŞ VE DAHA GÜÇLÜ PROMPT ---
        # Modele kim olduğunu ve ne yapması gerektiğini net bir şekilde söylüyoruz.
        prompt = """Sen yalnızca ve daima Türkçe cevap veren bir sağlık turizmi asistanısın.
Kullanıcının isteği doğrultusunda, Antalya'daki saç ekimi hakkında bilgi ver.
Cevabında şu konulara değin: FUE ve DHI yöntemlerinin farkları, ortalama Euro cinsinden fiyat aralığı, işlem süresi ve iyileşme süreci.
Cevabın kısa, anlaşılır ve tamamı Türkçe olsun. İngilizce hiçbir kelime kullanma."""
        # --- BİTİŞ ---
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }

        dispatcher.utter_message(text="💇 Saç ekimi hakkında detaylı bilgi hazırlıyorum, lütfen bekleyin...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=60, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=generated_text)
            else:
                dispatcher.utter_message(text="Yapay zekadan anlamlı bir cevap alamadım, lütfen tekrar deneyin.")

        except requests.exceptions.Timeout:
            logger.error("Ollama API zaman aşımına uğradı.")
            dispatcher.utter_message(text="⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen tekrar deneyin.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API hatası: {e}")
            dispatcher.utter_message(text="❌ Yapay zeka servisine şu anda ulaşılamıyor. Lütfen Ollama'nın çalıştığından emin olun.")

        return []

class ActionAskOllama(Action):
    def name(self) -> Text:
        return "action_ask_ollama"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get('text', '')
        logger.info(f"Ollama'ya genel soru soruluyor: '{user_message}'")

        prompt = f"Sen bir sağlık turizmi asistanısın. Kullanıcının şu sorusunu kısa ve net bir şekilde Türkçe yanıtla: '{user_message}'"
        
        data = {
            "model": "llama3", # Model adını 'llama3' olarak düzelttim
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=45, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=generated_text)
            else:
                dispatcher.utter_message(text="Üzgünüm, bu soruya şu anda cevap veremiyorum.")

        except requests.exceptions.Timeout:
            logger.error("Ollama API (genel soru) zaman aşımına uğradı.")
            dispatcher.utter_message(text="⏱️ Yapay zeka servisi yanıt vermekte gecikiyor.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API (genel soru) hatası: {e}")
            dispatcher.utter_message(text="❌ Yapay zeka servisine maalesef şu anda ulaşılamıyor.")

        return []