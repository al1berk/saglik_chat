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
        # Önce entity'leri kontrol et
        tedavi = next(tracker.get_latest_entity_values("tedavi"), None)
        sehir = next(tracker.get_latest_entity_values("sehir"), None)
        
        # Entity yoksa slot'tan al (sohbet geçmişinden)
        if not tedavi:
            tedavi = tracker.get_slot("tedavi")
        if not sehir:
            sehir = tracker.get_slot("sehir")
        
        # Şehir normalizasyonu
        if sehir:
            sehir = normalize_city(sehir)
        
        logger.info(f"🔍 Klinik arama: tedavi={tedavi}, sehir={sehir} (slot'tan: {tracker.get_slot('sehir')})")
        
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
        
        # Entity yoksa slot'tan al (sohbet geçmişinden)
        if not sehir:
            sehir = tracker.get_slot("sehir")
        if not otel_tipi:
            otel_tipi = tracker.get_slot("otel_tipi")
        
        # Şehir normalizasyonu
        if sehir:
            sehir = normalize_city(sehir)
        
        logger.info(f"🔍 Otel arama: sehir={sehir}, tip={otel_tipi} (slot'tan: {tracker.get_slot('sehir')})")
        
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

class ActionDisImplantDetaylari(Action):
    """Diş implantı bilgisi için Ollama'dan detaylı açıklama al"""
    
    def name(self) -> Text:
        return "action_dis_implant_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("🦷 Diş implantı bilgisi için Ollama'ya sorgu gönderiliyor...")

        prompt = """Sen profesyonel bir Türk sağlık turizmi danışmanısın. 

ÖNEMLİ: SADECE VE SADECE TÜRKÇE CEVAP VER!

Diş implantı tedavisi hakkında şu bilgileri kısa ve net şekilde açıkla:

1. Diş implantı nedir ve nasıl yapılır?
2. All-on-4 ve All-on-6 teknikleri nedir?
3. Tek diş vs çoklu diş implantı farkları
4. Ortalama tedavi ücreti: 400-800 Euro (tek diş), 3.500-6.000 Euro (All-on-4/6)
5. İşlem süresi: Tek diş 30-60 dakika, tam ağız 2-3 saat
6. İyileşme süresi: 3-6 ay (kemik entegrasyonu)
7. Paket içeriği: Panoramik röntgen, 3D tomografi, geçici protez, otel konaklaması dahil

Her maddeyi 2-3 cümle ile açıkla. Net, anlaşılır ve profesyonel bir dil kullan.
Toplam maksimum 10 cümle yaz."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 500,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "stop": ["English:", "In English:", "Translation:"]
            }
        }

        dispatcher.utter_message(text="🦷 Diş implantı hakkında detaylı bilgi hazırlıyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=f"🦷 **DİŞ IMPLANTI BİLGİLERİ:**\n\n{generated_text}")
                logger.info(f"✅ Ollama cevabı başarıyla alındı ({len(generated_text)} karakter)")
            else:
                dispatcher.utter_message(text="🦷 Üzgünüm, diş implantı bilgisi şu anda hazırlanamadı. Lütfen tekrar deneyin.")
                logger.warning("⚠️ Ollama boş cevap döndürdü")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen 'ollama serve' komutunu çalıştırın.")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama API zaman aşımı ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text=f"⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen biraz bekleyip tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")

        return [{"event": "slot", "name": "tedavi", "value": "diş implantı"}]

class ActionRinoplastiDetaylari(Action):
    """Rinoplasti (burun estetiği) bilgisi için Ollama'dan detaylı açıklama al"""
    
    def name(self) -> Text:
        return "action_rinoplasti_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("👃 Rinoplasti bilgisi için Ollama'ya sorgu gönderiliyor...")

        prompt = """Sen profesyonel bir Türk sağlık turizmi danışmanısın. 

ÖNEMLİ: SADECE VE SADECE TÜRKÇE CEVAP VER!

Rinoplasti (burun estetiği) tedavisi hakkında şu bilgileri kısa ve net şekilde açıkla:

1. Rinoplasti nedir ve nasıl yapılır?
2. Açık rinoplasti vs Kapalı rinoplasti farkları
3. Piezo tekniği nedir?
4. Ortalama tedavi ücreti: 2.500-4.500 Euro
5. İşlem süresi: 2-4 saat
6. İyileşme süresi: 7-10 gün (splint çıkarma), 6-12 ay (tam iyileşme)
7. Paket içeriği: Tüm testler, 5 yıldız otel, VIP transfer, kontroller dahil

Her maddeyi 2-3 cümle ile açıkla. Net, anlaşılır ve profesyonel bir dil kullan.
Toplam maksimum 10 cümle yaz."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 500,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "stop": ["English:", "In English:", "Translation:"]
            }
        }

        dispatcher.utter_message(text="👃 Rinoplasti hakkında detaylı bilgi hazırlıyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=f"👃 **RİNOPLASTİ BİLGİLERİ:**\n\n{generated_text}")
                logger.info(f"✅ Ollama cevabı başarıyla alındı ({len(generated_text)} karakter)")
            else:
                dispatcher.utter_message(text="👃 Üzgünüm, rinoplasti bilgisi şu anda hazırlanamadı. Lütfen tekrar deneyin.")
                logger.warning("⚠️ Ollama boş cevap döndürdü")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen 'ollama serve' komutunu çalıştırın.")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama API zaman aşımı ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text=f"⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen biraz bekleyip tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")

        return [{"event": "slot", "name": "tedavi", "value": "rinoplasti"}]

class ActionMideKucultmeDetaylari(Action):
    """Mide küçültme ameliyatı bilgisi için Ollama'dan detaylı açıklama al"""
    
    def name(self) -> Text:
        return "action_mide_kucultme_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("🏥 Mide küçültme bilgisi için Ollama'ya sorgu gönderiliyor...")

        prompt = """Sen profesyonel bir Türk sağlık turizmi danışmanısın. 

ÖNEMLİ: SADECE VE SADECE TÜRKÇE CEVAP VER!

Mide küçültme (bariatrik cerrahi) ameliyatı hakkında şu bilgileri kısa ve net şekilde açıkla:

1. Mide küçültme ameliyatı nedir?
2. Sleeve gastrektomi (tüp mide) vs Gastrik bypass farkları
3. Kimler için uygundur? (BMI > 35)
4. Ortalama tedavi ücreti: 3.500-5.500 Euro
5. İşlem süresi: 1-2 saat (laparoskopik)
6. Hastanede kalış: 3-4 gün, iyileşme: 2-3 hafta
7. Beklenen kilo kaybı: 1 yılda %60-70 fazla kilo
8. Paket içeriği: Tüm testler, diyet programı, otel, transfer dahil

Her maddeyi 2-3 cümle ile açıkla. Net, anlaşılır ve profesyonel bir dil kullan.
Toplam maksimum 12 cümle yaz."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 600,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "stop": ["English:", "In English:", "Translation:"]
            }
        }

        dispatcher.utter_message(text="🏥 Mide küçültme ameliyatı hakkında detaylı bilgi hazırlıyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=f"🏥 **MİDE KÜÇÜLTME BİLGİLERİ:**\n\n{generated_text}")
                logger.info(f"✅ Ollama cevabı başarıyla alındı ({len(generated_text)} karakter)")
            else:
                dispatcher.utter_message(text="🏥 Üzgünüm, mide küçültme bilgisi şu anda hazırlanamadı. Lütfen tekrar deneyin.")
                logger.warning("⚠️ Ollama boş cevap döndürdü")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen 'ollama serve' komutunu çalıştırın.")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama API zaman aşımı ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text=f"⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen biraz bekleyip tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")

        return [{"event": "slot", "name": "tedavi", "value": "mide küçültme"}]

class ActionLasikDetaylari(Action):
    """Lasik (göz lazer) ameliyatı bilgisi için Ollama'dan detaylı açıklama al"""
    
    def name(self) -> Text:
        return "action_lasik_detaylari"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("👁️ Lasik bilgisi için Ollama'ya sorgu gönderiliyor...")

        prompt = """Sen profesyonel bir Türk sağlık turizmi danışmanısın. 

ÖNEMLİ: SADECE VE SADECE TÜRKÇE CEVAP VER!

Lasik (göz lazer) ameliyatı hakkında şu bilgileri kısa ve net şekilde açıkla:

1. Lasik ameliyatı nedir ve nasıl yapılır?
2. Lasik, PRK ve Femtolasik farkları
3. Kimler için uygundur? (miyopi, hipermetropi, astigmat)
4. Ortalama tedavi ücreti: 1.500-2.500 Euro (her iki göz)
5. İşlem süresi: 15-20 dakika (her iki göz)
6. İyileşme süresi: 1-2 gün (görmede düzelme), 1 hafta (tam iyileşme)
7. Başarı oranı: %95+ hastada gözlüksüz yaşam
8. Paket içeriği: Tüm testler, kontroller, otel, transfer dahil

Her maddeyi 2-3 cümle ile açıkla. Net, anlaşılır ve profesyonel bir dil kullan.
Toplam maksimum 12 cümle yaz."""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 600,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "stop": ["English:", "In English:", "Translation:"]
            }
        }

        dispatcher.utter_message(text="👁️ Lasik ameliyatı hakkında detaylı bilgi hazırlıyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=f"👁️ **LASİK AMELİYATI BİLGİLERİ:**\n\n{generated_text}")
                logger.info(f"✅ Ollama cevabı başarıyla alındı ({len(generated_text)} karakter)")
            else:
                dispatcher.utter_message(text="👁️ Üzgünüm, lasik bilgisi şu anda hazırlanamadı. Lütfen tekrar deneyin.")
                logger.warning("⚠️ Ollama boş cevap döndürdü")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen 'ollama serve' komutunu çalıştırın.")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama API zaman aşımı ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text=f"⏱️ Yapay zeka servisi yanıt vermekte gecikiyor. Lütfen biraz bekleyip tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text=f"❌ Bir hata oluştu: {str(e)}")

        return [{"event": "slot", "name": "tedavi", "value": "lasik"}]

class ActionFiyatBilgisi(Action):
    """Fiyat bilgisi için context-aware cevap ver"""
    
    def name(self) -> Text:
        return "action_fiyat_bilgisi"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Slot'tan tedavi bilgisini al
        tedavi = tracker.get_slot("tedavi")
        tedavi_entity = next(tracker.get_latest_entity_values("tedavi"), None)
        
        if tedavi_entity:
            tedavi = tedavi_entity
        
        logger.info(f"💰 Fiyat bilgisi soruluyor - tedavi: {tedavi}")

        # Tedavi bazlı fiyat bilgileri
        fiyat_bilgileri = {
            "saç ekimi": "💇 **SAÇ EKİMİ FİYATLARI:**\n- FUE Tekniği: 2.500-3.500 Euro\n- DHI Tekniği: 3.000-4.000 Euro\n- Paket: 5 yıldız otel, VIP transfer, tüm kontroller dahil",
            "diş implantı": "🦷 **DİŞ IMPLANTI FİYATLARI:**\n- Tek Diş: 400-800 Euro\n- All-on-4: 3.500-5.000 Euro\n- All-on-6: 4.500-6.000 Euro\n- Paket: Otel konaklaması, testler dahil",
            "rinoplasti": "👃 **RİNOPLASTİ FİYATLARI:**\n- Açık/Kapalı Rinoplasti: 2.500-4.500 Euro\n- Piezo Tekniği: 3.500-5.000 Euro\n- Paket: 5 yıldız otel, VIP transfer, kontroller dahil",
            "mide küçültme": "🏥 **MİDE KÜÇÜLTME FİYATLARI:**\n- Sleeve Gastrektomi: 3.500-4.500 Euro\n- Gastrik Bypass: 4.000-5.500 Euro\n- Paket: 3-4 gün hastane, otel, diyet programı dahil",
            "lasik": "👁️ **LASİK AMELİYATI FİYATLARI:**\n- Klasik Lasik: 1.500-2.000 Euro\n- Femtolasik: 2.000-2.500 Euro (her iki göz)\n- Paket: Tüm testler, kontroller dahil"
        }

        if tedavi and any(key in tedavi.lower() for key in fiyat_bilgileri.keys()):
            for key, value in fiyat_bilgileri.items():
                if key in tedavi.lower():
                    dispatcher.utter_message(text=value)
                    return []
        
        # Genel fiyat bilgisi
        message = """💰 **GENEL FİYAT BİLGİLERİ:**

Türkiye'deki medikal turizm fiyatları, Avrupa ve ABD'ye göre %50-70 daha ekonomiktir.

**Popüler Tedaviler:**
🦷 Diş İmplantı: 400-800 Euro (tek)
💇 Saç Ekimi: 2.500-4.000 Euro
👃 Rinoplasti: 2.500-4.500 Euro
🏥 Mide Küçültme: 3.500-5.500 Euro
👁️ Lasik: 1.500-2.500 Euro

**Paket İçeriği:**
✅ Tüm ameliyat masrafları
✅ Otel konaklaması
✅ VIP havalimanı transferi
✅ Ameliyat öncesi/sonrası kontroller
✅ Tercümanlık hizmeti

Hangi tedavi için detaylı fiyat bilgisi almak istersiniz?"""
        
        dispatcher.utter_message(text=message)
        return []

class ActionSigortaBilgisi(Action):
    """Sigorta bilgisi ver"""
    
    def name(self) -> Text:
        return "action_sigorta_bilgisi"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("🏥 Sigorta bilgisi soruluyor...")

        message = """🏥 **SİGORTA BİLGİLERİ:**

**Türkiye'deki Medikal Turizm ve Sigorta:**

❌ **SGK (Sosyal Güvenlik Kurumu):**
Yurt dışından gelen hastalar için SGK kapsamı yoktur. Ancak Türk vatandaşları belirli koşullarda SGK ile tedavi olabilir.

✅ **Özel Sigorta:**
- Bazı uluslararası özel sağlık sigortaları Türkiye'deki tedavileri karşılayabilir
- Anlaşmalı kliniklerimiz: Allianz, Axa, Cigna
- Tedavi öncesi sigorta şirketinizle mutlaka iletişime geçin

💳 **Ödeme Seçenekleri:**
- Nakit (Euro, Dolar, TL)
- Kredi kartı (taksit imkanı)
- Banka havalesi

📋 **Fatura ve Raporlama:**
- Tüm tedaviler için detaylı fatura verilir
- Sigorta şirketinize sunabileceğiniz medikal raporlar hazırlanır
- Geri ödeme için gerekli evraklar sağlanır

Özel sigorta durumunuz için kliniklerimizle direkt iletişime geçmenizi öneririz."""
        
        dispatcher.utter_message(text=message)
        return []

class ActionRandevuBilgisi(Action):
    """Randevu alma bilgisi ver"""
    
    def name(self) -> Text:
        return "action_randevu_bilgisi"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("📅 Randevu bilgisi soruluyor...")

        message = """📅 **RANDEVU ALMA SÜRECİ:**

**Adım 1: İletişim**
📞 Klinikle direkt iletişime geçin
📧 E-posta ile başvuru yapın
💬 WhatsApp hattından yazın

**Adım 2: Ön Değerlendirme**
📸 Fotoğraf veya röntgen gönderin
📋 Medikal geçmişinizi paylaşın
🩺 Online konsültasyon alın (ücretsiz)

**Adım 3: Randevu Tarihi**
📅 Uygun tarih belirleyin
✈️ Uçak bileti alın
🏨 Otel rezervasyonu yapılır

**Adım 4: Türkiye'ye Geliş**
🚐 VIP havalimanı karşılama
🏥 Kliniğe transfer
👨‍⚕️ Doktor görüşmesi ve son kontroller

**Randevu Süresi:**
- Acil durumlar: 2-3 gün içinde
- Normal randevu: 1-2 hafta
- Yoğun dönemler: 3-4 hafta

**İletişim:**
Öncelikle hangi tedavi için randevu almak istediğinizi belirtin. Size en uygun kliniği önerebilirim!"""
        
        dispatcher.utter_message(text=message)
        return []