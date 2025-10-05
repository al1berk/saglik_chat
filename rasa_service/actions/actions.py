# actions/actions.py

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Adresleri - 127.0.0.1 KULLAN (localhost yerine!)
API_SERVICE_URL = "http://127.0.0.1:8000/api"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

PROXIES = {
    "http": None,
    "https": None,
}

# Timeout süreleri (saniye) - AGRESİF DÜŞÜRÜLDÜ
API_TIMEOUT = 5  # API istekleri için 5 saniye (30s → 5s)
OLLAMA_TIMEOUT = 30  # Ollama için 30 saniye (90s → 30s)

# Entity normalizasyon mapping
CITY_NORMALIZATION = {
    "antalyada": "Antalya",
    "antalya": "Antalya",
    "istanbulda": "İstanbul",
    "istanbul": "İstanbul",
    "izmirde": "İzmir",
    "izmir": "İzmir",
    "bursada": "Bursa",
    "bursa": "Bursa"
}

def normalize_city(city: str) -> str:
    """Şehir ismini normalize et"""
    if not city:
        return None
    city_lower = city.lower().strip()
    return CITY_NORMALIZATION.get(city_lower, city.title())

class ActionKlinikAra(Action):
    def name(self) -> Text:
        return "action_klinik_ara"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tedavi = next(tracker.get_latest_entity_values("tedavi"), None)
        sehir = next(tracker.get_latest_entity_values("sehir"), None)
        
        # Şehir normalizasyonu
        if sehir:
            sehir = normalize_city(sehir)
        
        logger.info(f"🔍 Klinik arama: tedavi={tedavi}, sehir={sehir}")
        
        try:
            # Doğru endpoint: /api/clinics/search
            api_url = f"{API_SERVICE_URL}/clinics/search"
            params = {}
            
            if tedavi:
                params["treatment"] = tedavi
            if sehir:
                params["city"] = sehir
            
            params["limit"] = 5
            
            logger.info(f"📡 API çağrısı: {api_url} | Params: {params}")
            
            response = requests.get(api_url, params=params, timeout=API_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            clinics = response.json()
            logger.info(f"✅ {len(clinics)} klinik bulundu")
            
            if clinics:
                message = f"🏥 **{len(clinics)} Klinik Buldum:**\n\n"
                for i, clinic in enumerate(clinics[:3], 1):
                    message += f"**{i}. {clinic.get('name', 'İsimsiz Klinik')}**\n"
                    message += f"   📍 {clinic.get('city', 'Şehir Belirtilmemiş')}\n"
                    message += f"   ⭐ Puan: {clinic.get('rating', 'N/A')}/5\n"
                    message += f"   📞 {clinic.get('phone', 'Tel yok')}\n"
                    
                    treatments = clinic.get('treatments', [])
                    if treatments:
                        message += f"   💉 Tedaviler: {', '.join(treatments[:3])}\n"
                    message += "\n"
                
                # Ollama ile doğal dil açıklaması ekle
                try:
                    ollama_response = self._get_ollama_recommendation(clinics[:3], sehir, tedavi)
                    if ollama_response:
                        message += f"\n💡 **Önerim:**\n{ollama_response}"
                except Exception as e:
                    logger.warning(f"Ollama önerisi alınamadı: {e}")
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="😔 Üzgünüm, aradığınız kriterlere uygun klinik bulamadım. Başka bir şehir veya tedavi deneyin.")
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ API servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Klinik arama servisi çalışmıyor. Lütfen API'nin çalıştığından emin olun.")
        except requests.exceptions.Timeout:
            logger.error("⏱️ API servisi zaman aşımı")
            dispatcher.utter_message(text="⏱️ Klinik arama servisi çok yavaş. Lütfen tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Beklenmeyen hata: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")
        
        return []
    
    def _get_ollama_recommendation(self, clinics: List[Dict], city: str, treatment: str) -> str:
        """Ollama'dan klinik önerisi al"""
        context = "Bulunan klinikler:\n"
        for i, clinic in enumerate(clinics, 1):
            context += f"{i}. {clinic.get('name')} - {clinic.get('city')} - Puan: {clinic.get('rating')}\n"
        
        prompt = f"""Sen bir sağlık turizmi danışmanısın. 
Kullanıcı {city if city else 'bir şehirde'} {treatment if treatment else 'tedavi'} arıyor.
Yukarıdaki klinikleri kısaca değerlendir ve hangisini önerirsin? (Maksimum 2-3 cümle, Türkçe)

{context}
"""
        
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={"model": "llama3", "prompt": prompt, "stream": False},
                timeout=30,
                proxies=PROXIES
            )
            if response.status_code == 200:
                return response.json().get('response', '').strip()[:300]  # Max 300 karakter
        except:
            pass
        return ""

class ActionOtelAra(Action):
    def name(self) -> Text:
        return "action_otel_ara"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        import time
        start_time = time.time()
        
        sehir = next(tracker.get_latest_entity_values("sehir"), None)
        otel_tipi = next(tracker.get_latest_entity_values("otel_tipi"), None)
        
        # Şehir normalizasyonu
        if sehir:
            sehir = normalize_city(sehir)
        
        logger.info(f"🔍 Otel arama: sehir={sehir}, tip={otel_tipi}")
        
        try:
            # Doğru endpoint: /api/hotels/search
            api_url = f"{API_SERVICE_URL}/hotels/search"
            params = {}
            
            if sehir:
                params["city"] = sehir
            if otel_tipi:
                params["hotel_type"] = otel_tipi
            
            params["limit"] = 5
            
            logger.info(f"📡 API çağrısı başlıyor: {api_url}")
            logger.info(f"📊 Params: {params}")
            logger.info(f"⏱️ Timeout: {API_TIMEOUT}s")
            
            # HTTP GET isteği
            response = requests.get(
                api_url, 
                params=params, 
                timeout=API_TIMEOUT, 
                proxies=PROXIES
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ API yanıt aldı: status={response.status_code}, süre={elapsed:.2f}s")
            
            response.raise_for_status()
            
            hotels = response.json()
            logger.info(f"✅ {len(hotels)} otel bulundu")
            
            if hotels:
                message = f"🏨 **{len(hotels)} Otel Buldum:**\n\n"
                for i, hotel in enumerate(hotels[:3], 1):
                    message += f"**{i}. {hotel.get('name', 'İsimsiz Otel')}**\n"
                    message += f"   📍 {hotel.get('city', 'Şehir Belirtilmemiş')}\n"
                    message += f"   ⭐ Puan: {hotel.get('rating', 'N/A')}/5\n"
                    message += f"   💰 Gecelik: ${hotel.get('price_per_night', 'N/A')}\n"
                    
                    features = hotel.get('features', [])
                    if features:
                        message += f"   ✨ Özellikler: {', '.join(features[:3])}\n"
                    message += "\n"
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="😔 Aradığınız kriterlere uygun otel bulamadım.")
                
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ API bağlantı hatası ({elapsed:.2f}s): {e}")
            logger.error(f"🔗 URL: {api_url}")
            dispatcher.utter_message(text="❌ Otel arama servisi çalışmıyor.")
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            logger.error(f"⏱️ API timeout ({elapsed:.2f}s / {API_TIMEOUT}s)")
            logger.error(f"🔗 URL: {api_url}")
            logger.error(f"❌ Hata detayı: {e}")
            dispatcher.utter_message(text=f"⏱️ Otel arama servisi yanıt vermekte gecikiyor ({API_TIMEOUT}s timeout). Lütfen tekrar deneyin.")
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ HTTP hatası ({elapsed:.2f}s): {e}")
            logger.error(f"🔗 URL: {api_url}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"📊 Response status: {e.response.status_code}")
                logger.error(f"📄 Response body: {e.response.text[:200]}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Beklenmeyen hata ({elapsed:.2f}s): {type(e).__name__} - {e}")
            logger.error(f"🔗 URL: {api_url}")
            import traceback
            logger.error(f"📚 Traceback: {traceback.format_exc()}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")
        
        return []

class ActionSacEkimiDetaylari(Action):
    def name(self) -> Text:
        return "action_sac_ekimi_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("💇 Saç ekimi bilgisi için Ollama'ya sorgu gönderiliyor...")

        # GÜÇLÜ TÜRKÇE PROMPT - Fallback yok, direkt Ollama cevabı
        prompt = """Sen profesyonel bir Türk sağlık turizmi danışmanısın. 

ÖNEMLİ: SADECE VE SADECE TÜRKÇE CEVAP VER! Hiçbir İngilizce kelime kullanma!

Antalya'daki saç ekimi tedavisi hakkında şu bilgileri kısa ve net şekilde açıkla:

1. FUE (Follicular Unit Extraction) tekniği nedir? Nasıl yapılır?
2. DHI (Direct Hair Implantation) tekniği nedir? Nasıl yapılır?
3. Bu iki teknik arasındaki temel farklar nelerdir?
4. Ortalama tedavi ücreti: 2.500-4.000 Euro arası
5. İşlem süresi: Genellikle 6-8 saat
6. İyileşme süresi: 7-10 gün
7. Paket içeriği: 5 yıldız otel konaklaması, VIP havalimanı transferi, tüm kontroller dahil

Her maddeyi 2-3 cümle ile açıkla. Net, anlaşılır ve profesyonel bir dil kullan.
Toplam maksimum 10 cümle yaz."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,  # Daha tutarlı ve deterministik
                "num_predict": 500,  # Daha uzun cevaplar için
                "top_p": 0.9,
                "repeat_penalty": 1.2,  # Tekrar önleme
                "stop": ["English:", "In English:", "Translation:"]  # İngilizce geçişi engelle
            }
        }

        dispatcher.utter_message(text="💇 Saç ekimi hakkında detaylı bilgi hazırlıyorum, lütfen bekleyin...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                # Direkt Ollama cevabını göster (fallback YOK!)
                dispatcher.utter_message(text=f"💇 **SAÇ EKİMİ BİLGİLERİ:**\n\n{generated_text}")
                logger.info(f"✅ Ollama cevabı başarıyla alındı ({len(generated_text)} karakter)")
            else:
                # Sadece boş cevap durumunda minimal fallback
                dispatcher.utter_message(text="💇 Üzgünüm, saç ekimi bilgisi şu anda hazırlanamadı. Lütfen tekrar deneyin veya daha spesifik bir soru sorun.")
                logger.warning("⚠️ Ollama boş cevap döndürdü")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen 'ollama serve' komutunu çalıştırın ve tekrar deneyin.")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama API zaman aşımı ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text=f"⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen biraz bekleyip tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")

        return []

class ActionAskOllama(Action):
    """Genel sorular için Ollama'ya sor"""
    
    def name(self) -> Text:
        return "action_ask_ollama"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get('text', '')
        logger.info(f"🤖 Ollama'ya genel soru: '{user_message}'")

        prompt = f"""Sen bir Türk sağlık turizmi asistanısın. 
Kullanıcının şu sorusunu kısa, net ve TÜRKÇE yanıtla: '{user_message}'

Yanıtın maksimum 3-4 cümle olsun."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 300
            }
        }

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=generated_text)
            else:
                dispatcher.utter_message(text="Üzgünüm, bu soruya şu anda cevap veremiyorum.")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text="Üzgünüm, şu anda size yardımcı olamıyorum.")

        return []