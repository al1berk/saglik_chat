# actions/actions.py

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests
import logging
import json
from datetime import datetime
from rasa_sdk.events import SlotSet, FollowupAction
import sys
import os

# MongoDB logger için path ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api_service.mongodb_logger import MongoDBLogger
from rasa_service.actions.api_clients import ClinicAPIClient, FlightAPIClient, HotelAPIClient


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Adresleri - 127.0.0.1 KULLAN (localhost yerine!)
API_SERVICE_URL = "http://127.0.0.1:8000/api"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

PROXIES = {
    "http": None,
    "https": None,
}


# API Client'ları başlat
clinic_client = ClinicAPIClient()
hotel_client = HotelAPIClient()
flight_client = FlightAPIClient()
# Timeout süreleri (saniye) - AGRESİF DÜŞÜRÜLDÜ
API_TIMEOUT = 5  # API istekleri için 5 saniye (30s → 5s)
OLLAMA_TIMEOUT = 30  # Ollama için 30 saniye (90s → 30s)

CITY_NORMALIZATION = {
    # Antalya
    "antalya": "Antalya",
    "antalyada": "Antalya",
    "antalya'da": "Antalya",
    "antalyaya": "Antalya",
    "antalya'ya": "Antalya",
    "antalyadan": "Antalya",
    "antalya'dan": "Antalya",
    "antalyanın": "Antalya",
    "antalya'nın": "Antalya",
    
    # İstanbul
    "istanbul": "İstanbul",
    "istanbulda": "İstanbul",
    "istanbul'da": "İstanbul",
    "istanbula": "İstanbul",
    "istanbul'a": "İstanbul",
    "istanbuldan": "İstanbul",
    "istanbul'dan": "İstanbul",
    "istanbulun": "İstanbul",
    "istanbul'un": "İstanbul",

    # İzmir
    "izmir": "İzmir",
    "izmirde": "İzmir",
    "izmir'de": "İzmir",
    "izmire": "İzmir",
    "izmir'e": "İzmir",
    "izmirden": "İzmir",
    "izmir'den": "İzmir",
    "izmirin": "İzmir",
    "izmir'in": "İzmir",

    # Ankara
    "ankara": "Ankara",
    "ankarada": "Ankara",
    "ankara'da": "Ankara",
    "ankaraya": "Ankara",
    "ankara'ya": "Ankara",
    "ankaradan": "Ankara",
    "ankara'dan": "Ankara",
    "ankaranın": "Ankara",
    "ankara'nın": "Ankara"
}

def normalize_city(city: str) -> str:
    """Şehir ismini normalize et"""
    if not city:
        return None
    city_lower = city.lower().strip()
    return CITY_NORMALIZATION.get(city_lower, city.title())



class ActionAskOllama(Action):
    """Genel sorular için Ollama'ya sor - Rasa'nın anlayamadığı sorular buraya yönlendirilir"""
    
    def name(self) -> Text:
        return "action_ask_ollama"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get('text', '')
        logger.info(f"🤖 Ollama'ya genel soru (fallback): '{user_message}'")

        # ✅ TÜM CONTEXT BİLGİLERİNİ TOPLA
        # 1. Slot'lardan kullanıcı bilgileri
        tedavi_adi = tracker.get_slot("tedavi_adi")
        tedavi_turu = tracker.get_slot("tedavi_turu")
        sehir = tracker.get_slot("sehir")
        bolge = tracker.get_slot("bolge")
        butce = tracker.get_slot("butce")
        klinik_adi = tracker.get_slot("klinik_adi")
        tarih = tracker.get_slot("tarih")
        otel_kategori = tracker.get_slot("otel_kategori")
        ucus_sinifi = tracker.get_slot("ucus_sinifi")
        
        # 2. Sohbet geçmişini al (son 5 mesaj)
        conversation_history = []
        for event in list(tracker.events)[-10:]:  # Son 10 event'e bak
            if event.get('event') == 'user':
                conversation_history.append(f"Kullanıcı: {event.get('text', '')}")
            elif event.get('event') == 'bot':
                conversation_history.append(f"Bot: {event.get('text', '')[:100]}...")  # İlk 100 karakter
        
        # 3. Context bilgisini zengin şekilde oluştur
        context_info = "\n\n📋 **KULLANICI PROFİLİ:**\n"
        
        if tedavi_adi or tedavi_turu:
            context_info += f"• Tedavi: {tedavi_adi or tedavi_turu or 'Belirtilmemiş'}\n"
        if sehir:
            context_info += f"• Şehir: {sehir}\n"
        if bolge:
            context_info += f"• Bölge: {bolge}\n"
        if butce:
            context_info += f"• Bütçe: {butce}\n"
        if klinik_adi:
            context_info += f"• İlgilenilen Klinik: {klinik_adi}\n"
        if tarih:
            context_info += f"• Tarih: {tarih}\n"
        if otel_kategori:
            context_info += f"• Otel Tercihi: {otel_kategori}\n"
        if ucus_sinifi:
            context_info += f"• Uçuş Sınıfı: {ucus_sinifi}\n"
        
        # Eğer hiç bilgi yoksa
        if context_info == "\n\n📋 **KULLANICI PROFİLİ:**\n":
            context_info = "\n\n📋 Kullanıcı henüz profil bilgisi paylaşmadı.\n"
        
        # 4. Son 3 mesajı ekle
        if conversation_history:
            context_info += f"\n💬 **SON MESAJLAR:**\n"
            for msg in conversation_history[-3:]:
                context_info += f"{msg}\n"

        # ✅ GELİŞTİRİLMİŞ PROMPT - Medikal Turizm Odaklı
        prompt = f"""Sen Türkiye'nin lider sağlık turizmi şirketinin AI asistanısın. Adın "Sağlık Turizmi AI Asistan".

🎯 **UZMANLIKLARIN:**
- Türkiye'deki tüm medikal tedavi türleri (diş, estetik, göz, ortopedi, kardiyoloji, obezite)
- Klinik ve hastane önerileri (Antalya, İstanbul, İzmir, Ankara)
- Konaklama ve ulaşım planlaması
- Fiyat bilgilendirme ve paket önerileri
- Hasta hakları ve yasal süreçler

📌 **ÖNEMLİ KURALLAR:**
1. ✅ SADECE TÜRKÇE YANIT VER (hiç İngilizce kullanma)
2. ✅ Kısa, samimi ve profesyonel ol (maksimum 5-6 cümle)
3. ✅ Sohbet akışını sürdür - context'i kullan
4. ❌ Kesin tanı/tedavi önerisi YAPMA - genel bilgi ver
5. ❌ Fiyat sorulursa "ortalama aralıklar" ver (kesin fiyat verme)
6. ✅ Kullanıcının ihtiyacını netleştirici sorular sor

{context_info}

🤔 **ŞİMDİKİ SORU:** {user_message}

💡 **CEVABINI YAZ (Türkçe, samimi, yardımcı):**"""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,  # Biraz daha yaratıcı
                "num_predict": 500,  # Daha uzun cevaplar
                "top_p": 0.9,
                "repeat_penalty": 1.3,
                "stop": ["KULLANICI", "USER:", "English:", "In English:", "Kullanıcı:", "SORU:"]
            }
        }

        dispatcher.utter_message(text="🤔 Düşünüyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                # Temizlik: Gereksiz başlıkları kaldır
                generated_text = generated_text.replace("💡 CEVABINI YAZ:", "").strip()
                generated_text = generated_text.replace("CEVAP:", "").strip()
                
                dispatcher.utter_message(text=f"💡 {generated_text}")
                logger.info(f"✅ Ollama fallback cevabı: {len(generated_text)} karakter")
                
                # ✅ Context'i güncelle - bütçe, tarih gibi bilgileri slot'a kaydet
                slots_to_set = []
                
                # Basit entity extraction (rakamlar bütçe olabilir)
                import re
                numbers = re.findall(r'\b\d{4,5}\b', user_message)
                if numbers and not butce:
                    potential_budget = numbers[0]
                    slots_to_set.append(SlotSet("butce", potential_budget))
                    logger.info(f"📊 Bütçe slot'una kaydedildi: {potential_budget}")
                
                return slots_to_set
            else:
                dispatcher.utter_message(text="Üzgünüm, bu soruya şu anda cevap veremiyorum. Daha spesifik sorular sorabilirsiniz:\n\n💡 Örnek sorular:\n• 'Antalya'da diş implantı kliniği'\n• 'Rinoplasti fiyatları'\n• 'Göz ameliyatı sonrası bakım'\n• 'Otel önerileri'")
                return []

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi şu anda çalışmıyor.\n\n✅ Şunları deneyebilirsiniz:\n• 'Antalya'da klinik ara'\n• 'Tedavi paketleri'\n• 'Fiyat bilgisi'")
            return []
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama timeout ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text="⏱️ Cevap hazırlanırken zaman aşımı. Lütfen tekrar deneyin veya daha spesifik soru sorun.")
            return []
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text="Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen:\n• Tedavi türü belirtin\n• Şehir seçin\n• Bütçe bilgisi verin\n\nVe tekrar deneyin!")
            return []

class ActionLogConversation(Action):
    """
    HER MESAJDA ÇALIŞIR - MongoDB'ye log atar
    Bu action'ı domain.yml'de tanımlamanız gerekiyor
    """
    
    def name(self) -> Text:
        return "action_log_conversation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # MongoDB logger başlat
        mongo_logger = MongoDBLogger()
        
        try:
            # User bilgilerini al
            user_id = tracker.sender_id
            latest_message = tracker.latest_message
            
            # Intent ve entities
            intent_data = latest_message.get('intent', {})
            intent_name = intent_data.get('name')
            confidence = intent_data.get('confidence', 0.0)
            entities = latest_message.get('entities', [])
            
            # User mesajını kaydet
            if latest_message.get('text'):
                mongo_logger.log_message(
                    user_id=user_id,
                    sender="user",
                    text=latest_message['text'],
                    intent=intent_name,
                    entities=entities,
                    confidence=confidence
                )
                
                logger.info(f"✅ MongoDB'ye kaydedildi: {user_id} - {intent_name}")
            
            # User profili güncelle (entity'lerden bilgi çıkar)
            user_updates = {}
            for entity in entities:
                entity_name = entity.get('entity')
                entity_value = entity.get('value')
                
                # Eğer kişisel bilgi entity'si ise profili güncelle
                if entity_name in ['yas', 'age']:
                    user_updates['age'] = int(entity_value) if isinstance(entity_value, (int, str)) else None
                elif entity_name in ['cinsiyet', 'gender']:
                    user_updates['gender'] = entity_value
                elif entity_name in ['isim', 'name']:
                    user_updates['name'] = entity_value
                elif entity_name in ['hastalik', 'health_condition']:
                    # Health conditions'ı array olarak tut
                    existing_user = mongo_logger.get_user(user_id)
                    health_conditions = existing_user.get('health_conditions', []) if existing_user else []
                    if entity_value not in health_conditions:
                        health_conditions.append(entity_value)
                    user_updates['health_conditions'] = health_conditions
            
            # Preferences güncelle (tedavi, şehir, bütçe vb.)
            preferences = {}
            for entity in entities:
                entity_name = entity.get('entity')
                entity_value = entity.get('value')
                
                if entity_name in ['tedavi_adi', 'treatment']:
                    preferences['treatment'] = entity_value
                elif entity_name in ['sehir', 'city']:
                    preferences['city'] = entity_value
                elif entity_name in ['butce', 'budget']:
                    preferences['budget'] = entity_value
                elif entity_name in ['bolge', 'region']:
                    preferences['region'] = entity_value
            
            if preferences:
                user_updates['preferences'] = preferences
            
            # Eğer güncellenecek bilgi varsa user'ı güncelle
            if user_updates:
                user_updates['user_id'] = user_id
                mongo_logger.upsert_user(user_updates)
                logger.info(f"✅ User profili güncellendi: {user_id}")
        
        except Exception as e:
            logger.error(f"❌ MongoDB logging hatası: {e}")
        
        finally:
            mongo_logger.close()
        
        return []


class ActionLogBotResponse(Action):
    """
    Bot cevabını MongoDB'ye kaydet
    """
    
    def name(self) -> Text:
        return "action_log_bot_response"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mongo_logger = MongoDBLogger()
        
        try:
            user_id = tracker.sender_id
            
            # Son bot action'ını al
            events = tracker.events
            last_bot_action = None
            last_bot_message = None
            
            for event in reversed(events):
                if event.get('event') == 'action':
                    last_bot_action = event.get('name')
                    break
                elif event.get('event') == 'bot':
                    last_bot_message = event.get('text')
                    if last_bot_action:
                        break
            
            # Bot mesajını kaydet
            if last_bot_message:
                mongo_logger.log_message(
                    user_id=user_id,
                    sender="bot",
                    text=last_bot_message,
                    bot_action=last_bot_action
                )
                logger.info(f"✅ Bot cevabı kaydedildi: {last_bot_action}")
        
        except Exception as e:
            logger.error(f"❌ Bot response logging hatası: {e}")
        
        finally:
            mongo_logger.close()
        
        return []


class ActionSaveUserProfile(Action):
    """
    User profili kaydetme action'ı (önceki kodunuzda vardı)
    Şimdi MongoDB'ye kaydediyor
    """
    
    def name(self) -> Text:
        return "action_save_user_profile"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mongo_logger = MongoDBLogger()
        
        try:
            user_id = tracker.sender_id
            
            # Slot'lardan user bilgilerini topla
            user_data = {
                "user_id": user_id,
                "name": tracker.get_slot("user_name"),
                "age": tracker.get_slot("yas"),
                "gender": tracker.get_slot("cinsiyet"),
                "preferences": {
                    "treatment": tracker.get_slot("tedavi_adi"),
                    "city": tracker.get_slot("sehir"),
                    "region": tracker.get_slot("bolge"),
                    "budget": tracker.get_slot("butce"),
                    "hotel_category": tracker.get_slot("otel_kategori"),
                    "flight_class": tracker.get_slot("ucus_sinifi")
                }
            }
            
            # Health conditions ekle
            hastalik = tracker.get_slot("hastalik")
            if hastalik:
                user_data["health_conditions"] = [hastalik] if isinstance(hastalik, str) else hastalik
            
            # MongoDB'ye kaydet
            mongo_logger.upsert_user(user_data)
            
            dispatcher.utter_message(text="✅ Bilgileriniz güvenle kaydedildi.")
            logger.info(f"✅ User profili MongoDB'ye kaydedildi: {user_id}")
        
        except Exception as e:
            logger.error(f"❌ User profile kaydetme hatası: {e}")
            dispatcher.utter_message(text="⚠️ Bilgileriniz kaydedilirken bir sorun oluştu.")
        
        finally:
            mongo_logger.close()
        
        return []


class ActionScheduleAppointment(Action):
    """
    Randevu oluştur ve MongoDB'ye booking olarak kaydet
    """
    
    def name(self) -> Text:
        return "action_schedule_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mongo_logger = MongoDBLogger()
        
        try:
            user_id = tracker.sender_id
            
            # Booking bilgilerini slot'lardan topla
            booking_data = {
                "user_id": user_id,
                "clinic_name": tracker.get_slot("klinik_adi") or "Belirtilmedi",
                "treatment": tracker.get_slot("tedavi_adi") or "Belirtilmedi",
                "hotel_name": tracker.get_slot("otel_kategori") or "Belirtilecek",
                "appointment_date": tracker.get_slot("tarih") or "Planlanacak",
                "status": "pending",
                "notes": f"Bütçe: {tracker.get_slot('butce')}"
            }
            
            # MongoDB'ye kaydet
            booking_id = mongo_logger.create_booking(booking_data)
            
            message = f"✅ Randevunuz oluşturuldu!\n\n"
            message += f"📋 Booking ID: {booking_id}\n"
            message += f"🏥 Klinik: {booking_data['clinic_name']}\n"
            message += f"💉 Tedavi: {booking_data['treatment']}\n"
            message += f"📅 Tarih: {booking_data['appointment_date']}\n\n"
            message += f"📧 Detaylı bilgilendirme e-posta adresinize gönderilecektir.\n"
            message += f"📱 Koordinatörümüz 24 saat içinde sizinle iletişime geçecektir."
            
            dispatcher.utter_message(text=message)
            logger.info(f"✅ Booking oluşturuldu: {booking_id}")
        
        except Exception as e:
            logger.error(f"❌ Appointment scheduling hatası: {e}")
            dispatcher.utter_message(text="⚠️ Randevu oluşturulurken bir sorun oluştu.")
        
        finally:
            mongo_logger.close()
        
        return []








# ============ FİYAT HESAPLAMA FONKSİYONU ============
def calculate_treatment_price(treatment_name, clinic_rating):
    """Tedavi fiyatını hesapla"""
    base_prices = {
        "dental implant": 1500,
        "rhinoplasty": 3500,
        "cataract": 2000,
        "sleeve gastrectomy": 4500,
        "knee replacement": 8000,
        "laser varicose vein": 1800,
        "teeth whitening": 300,
        "botox": 400,
        "face lift": 5000,
        "breast surgery": 4000
    }
    
    base_price = base_prices.get(treatment_name.lower(), 2000)
    # Klinik rating'e göre fiyat artışı
    rating_multiplier = 1 + (clinic_rating - 4.5) * 0.2
    
    return int(base_price * rating_multiplier)

def calculate_hotel_price(hotel_info, nights=7):
    """Otel fiyatını hesapla"""
    base_prices = {
        "standard": 100,
        "premium": 200,
        "luxury": 400
    }
    
    price_per_night = base_prices.get(hotel_info.get("price_range", "standard"), 150)
    return price_per_night * nights

def calculate_flight_price(flight_class, flight_type):
    """Uçuş fiyatını hesapla"""
    base_prices = {
        "economy": 300,
        "business": 1200
    }
    
    price = base_prices.get(flight_class, 300)
    if flight_type == "direct":
        price *= 1.3
    
    return int(price)


# ============ CUSTOM ACTIONS ============

class ActionSearchClinicsByTreatment(Action):
    """Tedavi türüne göre klinik ara - API Client kullanıyor"""
    
    def name(self) -> Text:
        return "action_search_clinics_by_treatment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        tedavi_adi = tracker.get_slot("tedavi_adi")
        tedavi_turu = tracker.get_slot("tedavi_turu")
        sehir = normalize_city(tracker.get_slot("sehir"))
        
        # Tedavi türünü belirle
        if not tedavi_turu and tedavi_adi:
            dental_treatments = ["implant", "whitening", "veneers", "orthodontics", "root canal"]
            aesthetic_treatments = ["rhinoplasty", "botox", "face lift", "breast"]
            eye_treatments = ["cataract", "glaucoma", "retinal"]
            
            tedavi_lower = tedavi_adi.lower()
            if any(t in tedavi_lower for t in dental_treatments):
                tedavi_turu = "dental"
            elif any(t in tedavi_lower for t in aesthetic_treatments):
                tedavi_turu = "aesthetic"
            elif any(t in tedavi_lower for t in eye_treatments):
                tedavi_turu = "eye_care"
        
        try:
            response = clinic_client.search_clinics(
                treatment_type=tedavi_turu,
                city=sehir,
                treatment_name=tedavi_adi
            )
            
            clinics = response.get("results", [])
            
            if clinics:
                message = f"✅ {sehir} için {len(clinics)} klinik bulundu!\n\n"
                
                for clinic in clinics[:3]:  # İlk 3 klinik göster
                    message += f"🏥 **{clinic['name']}**\n"
                    message += f"   📍 {clinic['district']}\n"
                    message += f"   ⭐ {clinic['rating']}/5.0\n"
                    message += f"   💉 Tedaviler: {', '.join(clinic['treatments'][:3])}\n\n"
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(
                    text=f"Üzgünüm, {sehir}'da bu tedavi için klinik bulunamadı."
                )
                
        except Exception as e:
            logger.error(f"❌ Klinik arama hatası: {e}")
            dispatcher.utter_message(
                text="⚠️ Klinik bilgileri alınırken bir hata oluştu."
            )
        
        return [SlotSet("tedavi_turu", tedavi_turu)]


class ActionSearchClinicsByLocation(Action):
    """Lokasyona göre klinik ara"""
    
    def name(self) -> Text:
        return "action_search_clinics_by_location"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        sehir = tracker.get_slot("sehir")
        bolge = tracker.get_slot("bolge")
        
        message = f"📍 {sehir}"
        if bolge:
            message += f" - {bolge} bölgesi"
        message += " için klinikler aranıyor..."
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionSearchHotelsByRegion(Action):
    """Bölgeye göre otel ara - API Client kullanıyor"""
    
    def name(self) -> Text:
        return "action_search_hotels_by_region"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        bolge = tracker.get_slot("bolge")
        otel_kategori = tracker.get_slot("otel_kategori")
        
        # Yıldız sayısını belirle
        stars = 5 if otel_kategori and "5" in otel_kategori else 4
        
        # ✅ API CLIENT KULLAN
        try:
            response = hotel_client.search_hotels(
                region=bolge,
                stars=stars
            )
            
            hotels = response.get("results", [])
            
            if hotels:
                message = f"🏨 {bolge} bölgesinde {len(hotels)} otel bulundu!\n\n"
                
                for hotel in hotels[:3]:  # İlk 3 otel göster
                    message += f"🏨 **{hotel['name']}**\n"
                    message += f"   {'⭐' * hotel['stars']}\n"
                    message += f"   💰 {hotel.get('price_per_night', 'Fiyat bilgisi yok')} EUR/gece\n"
                    message += f"   ✨ {', '.join(hotel['features'][:3])}\n\n"
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(
                    text=f"Üzgünüm, {bolge}'de uygun otel bulunamadı."
                )
                
        except Exception as e:
            logger.error(f"❌ Otel arama hatası: {e}")
            dispatcher.utter_message(
                text="⚠️ Otel bilgileri alınırken bir hata oluştu."
            )
        
        return []


class ActionGenerateBundleRecommendation(Action):
    """Yapay zeka destekli paket önerisi oluştur - API Client kullanıyor"""
    
    def name(self) -> Text:
        return "action_generate_bundle_recommendation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Kullanıcı bilgilerini topla
        user_profile = {
            "tedavi_turu": tracker.get_slot("tedavi_turu"),
            "tedavi_adi": tracker.get_slot("tedavi_adi"),
            "sehir": normalize_city(tracker.get_slot("sehir")),
            "bolge": tracker.get_slot("bolge"),
            "tarih": tracker.get_slot("tarih"),
            "butce": tracker.get_slot("butce"),
            "otel_kategori": tracker.get_slot("otel_kategori"),
            "ucus_sinifi": tracker.get_slot("ucus_sinifi") or "economy",
            "ucus_tipi": tracker.get_slot("ucus_tipi") or "connecting"
        }
        
        dispatcher.utter_message(text="🔍 Sizin için en uygun paketler hazırlanıyor...")
        
        try:
            # ✅ API CLIENT'LARI KULLAN
            # 1. Klinik ara
            clinic_response = clinic_client.search_clinics(
                treatment_type=user_profile["tedavi_turu"],
                city=user_profile["sehir"]
            )
            clinics = clinic_response.get("results", [])[:3]
            
            # 2. Otel ara
            hotel_response = hotel_client.search_hotels(
                region=user_profile["bolge"] or "Lara",
                stars=5
            )
            hotels = hotel_response.get("results", [])[:3]
            
            # 3. Uçuş ara
            flight_response = flight_client.search_flights(
                flight_class=user_profile["ucus_sinifi"]
            )
            flights = flight_response.get("results", [])[:3]
            
            # Paketleri oluştur
            bundles = []
            for i in range(min(3, len(clinics))):
                clinic = clinics[i] if i < len(clinics) else clinics[0]
                hotel = hotels[i] if i < len(hotels) else hotels[0]
                flight = flights[i] if i < len(flights) else flights[0]
                
                # Fiyat hesapla
                treatment_price = calculate_treatment_price(
                    user_profile.get("tedavi_adi", "dental treatment"),
                    clinic.get("rating", 4.5)
                )
                hotel_price = calculate_hotel_price(hotel, nights=7)
                flight_price = flight.get("price", 300)
                transfer_price = 150
                
                total_price = treatment_price + hotel_price + (flight_price * 2) + transfer_price
                
                bundles.append({
                    "name": f"Paket {i+1} - {['Ekonomik', 'Standart', 'Premium'][i]}",
                    "clinic": clinic["name"],
                    "clinic_rating": clinic["rating"],
                    "hotel": hotel["name"],
                    "hotel_stars": hotel["stars"],
                    "flight": flight.get("airline", "Turkish Airlines"),
                    "treatment_price": treatment_price,
                    "hotel_price": hotel_price,
                    "flight_price": flight_price * 2,
                    "transfer_price": transfer_price,
                    "total_price": total_price,
                    "currency": "EUR"
                })
            
            # Paketleri göster
            message = "🎁 **Sizin İçin Özel Hazırlanan Paketler:**\n\n"
            
            for bundle in bundles:
                message += f"**{bundle['name']}** - {bundle['total_price']} {bundle['currency']}\n"
                message += f"🏥 Klinik: {bundle['clinic']} (⭐{bundle['clinic_rating']})\n"
                message += f"🏨 Otel: {bundle['hotel']} ({'⭐' * bundle['hotel_stars']})\n"
                message += f"✈️ Uçuş: {bundle['flight']}\n"
                message += f"💰 Detaylar:\n"
                message += f"   • Tedavi: {bundle['treatment_price']} EUR\n"
                message += f"   • Konaklama (7 gece): {bundle['hotel_price']} EUR\n"
                message += f"   • Uçuş (Gidiş-Dönüş): {bundle['flight_price']} EUR\n"
                message += f"   • Transfer: {bundle['transfer_price']} EUR\n"
                message += f"━━━━━━━━━━━━━━━━━\n\n"
            
            message += "✅ Tüm paketler şunları içerir:\n"
            message += "• Havalimanı karşılama ve transferler\n"
            message += "• 7/24 Türkçe asistan desteği\n"
            message += "• Ön konsültasyon\n"
            message += "• Kontrol muayeneleri\n\n"
            message += "Hangi paketi seçmek istersiniz?"
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            logger.error(f"❌ Paket oluşturma hatası: {e}")
            dispatcher.utter_message(
                text="⚠️ Paket hazırlanırken bir hata oluştu. Lütfen tekrar deneyin."
            )
        
        return []


class ActionCalculatePackagePrice(Action):
    """Paket fiyatını hesapla ve göster"""
    
    def name(self) -> Text:
        return "action_calculate_package_price"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        tedavi_adi = tracker.get_slot("tedavi_adi") or "dental treatment"
        
        # Basit fiyat hesaplama
        base_price = calculate_treatment_price(tedavi_adi, 4.7)
        hotel_price = 700  # 7 gece ortalama
        flight_price = 600  # Gidiş-dönüş
        transfer_price = 150
        
        total = base_price + hotel_price + flight_price + transfer_price
        
        message = f"💰 **Fiyat Detayları:**\n\n"
        message += f"• Tedavi: {base_price} EUR\n"
        message += f"• Otel (7 gece): {hotel_price} EUR\n"
        message += f"• Uçuş: {flight_price} EUR\n"
        message += f"• Transfer: {transfer_price} EUR\n"
        message += f"━━━━━━━━━━━━━━━━━\n"
        message += f"**TOPLAM: {total} EUR**\n\n"
        message += f"✨ Ödeme seçenekleri:\n"
        message += f"• Peşin ödeme (5% indirim)\n"
        message += f"• 3 taksit (komisyonsuz)\n"
        message += f"• 6-12 taksit seçenekleri"
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionProvideClinicDetails(Action):
    """Klinik detaylarını göster - API Client kullanıyor"""
    
    def name(self) -> Text:
        return "action_provide_clinic_details"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        klinik_adi = tracker.get_slot("klinik_adi")
        
        if not klinik_adi:
            dispatcher.utter_message(text="Lütfen klinik adını belirtin.")
            return []
        
        try:
            # ✅ API CLIENT KULLAN - Tüm klinikleri ara
            response = clinic_client.search_clinics(
                treatment_type=None,  # Tüm kategoriler
                city=None,            # Tüm şehirler
                treatment_name=None   # Tüm tedaviler
            )
            
            all_clinics = response.get("results", [])
            
            # Klinik adına göre filtrele
            clinic_found = None
            for clinic in all_clinics:
                if clinic["name"].lower() == klinik_adi.lower():
                    clinic_found = clinic
                    break
                # Kısmi eşleşme de kontrol et
                elif klinik_adi.lower() in clinic["name"].lower():
                    clinic_found = clinic
                    break
            
            if clinic_found:
                message = f"🏥 **{clinic_found['name']}**\n\n"
                message += f"📍 Adres: {clinic_found.get('address', 'Belirtilmemiş')}\n"
                message += f"🏙️ Şehir: {clinic_found.get('city', 'N/A')}\n"
                message += f"📌 İlçe: {clinic_found.get('district', 'N/A')}\n"
                message += f"⭐ Rating: {clinic_found.get('rating', 0)}/5.0\n"
                
                if 'accreditations' in clinic_found:
                    message += f"🏆 Akreditasyonlar: {', '.join(clinic_found['accreditations'])}\n"
                
                if 'languages' in clinic_found:
                    message += f"🌍 Diller: {', '.join(clinic_found['languages'])}\n"
                
                message += f"\n💉 **Tedaviler:**\n"
                treatments = clinic_found.get('treatments', [])
                for treatment in treatments[:8]:  # İlk 8 tedavi
                    message += f"• {treatment}\n"
                
                if len(treatments) > 8:
                    message += f"• ve {len(treatments) - 8} tedavi daha...\n"
                
                message += f"\n💰 Fiyat Aralığı: {clinic_found.get('price_range', 'Standart').title()}\n"
                message += f"\n📞 Randevu almak için bize ulaşın!"
                
                dispatcher.utter_message(text=message)
            else:
                # Klinik bulunamadı, alternatif öner
                message = f"Üzgünüm, '{klinik_adi}' adlı klinik bulunamadı.\n\n"
                message += "✅ Şunları deneyebilirsiniz:\n"
                message += "• Klinik adını tam olarak yazın\n"
                message += "• Tedavi türü ve şehir belirtin\n"
                message += "• Örnek: 'Antalya'da diş kliniği'\n\n"
                
                # İlk 3 kliniği öneri olarak göster
                if all_clinics:
                    message += "📍 **Popüler Kliniklerimiz:**\n"
                    for clinic in all_clinics[:3]:
                        message += f"• {clinic['name']} ({clinic.get('city', 'Antalya')})\n"
                
                dispatcher.utter_message(text=message)
        
        except Exception as e:
            logger.error(f"❌ Klinik detay hatası: {e}")
            dispatcher.utter_message(
                text="⚠️ Klinik bilgileri alınırken bir hata oluştu. Lütfen tekrar deneyin."
            )
        
        return []


class ActionSaveUserProfile(Action):
    """Kullanıcı profilini kaydet"""
    
    def name(self) -> Text:
        return "action_save_user_profile"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_profile = {
            "user_name": tracker.get_slot("user_name"),
            "yas": tracker.get_slot("yas"),
            "cinsiyet": tracker.get_slot("cinsiyet"),
            "hastalik": tracker.get_slot("hastalik"),
            "saglik_durumu": tracker.get_slot("saglik_durumu"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Veritabanına kaydetme simülasyonu
        # Gerçek uygulamada database API kullanılacak
        
        dispatcher.utter_message(text="✅ Bilgileriniz güvenle kaydedildi.")
        
        return []


class ActionScheduleAppointment(Action):
    """Randevu planla"""
    
    def name(self) -> Text:
        return "action_schedule_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        klinik_adi = tracker.get_slot("klinik_adi")
        tarih = tracker.get_slot("tarih")
        tedavi_adi = tracker.get_slot("tedavi_adi")
        
        # Randevu API çağrısı simülasyonu
        
        message = f"✅ Randevunuz oluşturuldu!\n\n"
        message += f"🏥 Klinik: {klinik_adi or 'Seçilecek'}\n"
        message += f"💉 Tedavi: {tedavi_adi or 'Belirtilecek'}\n"
        message += f"📅 Tarih: {tarih or 'Planlanacak'}\n\n"
        message += f"📧 Detaylı bilgilendirme e-posta adresinize gönderilecektir.\n"
        message += f"📱 Koordinatörümüz 24 saat içinde sizinle iletişime geçecektir."
        
        dispatcher.utter_message(text=message)
        
        return []


class ValidateUserBudget(Action):
    """Kullanıcı bütçesini doğrula"""
    
    def name(self) -> Text:
        return "validate_user_budget"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        butce = tracker.get_slot("butce")
        
        if butce:
            # Bütçeden sayısal değer çıkar
            import re
            numbers = re.findall(r'\d+', str(butce))
            
            if numbers:
                budget_value = int(numbers[0])
                
                if budget_value < 2000:
                    message = "💡 Belirttiğiniz bütçe için ekonomik paketlerimiz mevcut. "
                    message += "Daha fazla seçenek için bütçenizi artırabilir veya ödeme planlarımızdan yararlanabilirsiniz."
                    dispatcher.utter_message(text=message)
                elif budget_value > 15000:
                    message = "👑 Premium ve lüks paketlerimizle size en iyi hizmeti sunabiliriz!"
                    dispatcher.utter_message(text=message)
        
        return []


class ValidateTreatmentCompatibility(Action):
    """Tedavi uyumluluğunu kontrol et"""
    
    def name(self) -> Text:
        return "validate_treatment_compatibility"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        hastalik = tracker.get_slot("hastalik")
        tedavi_adi = tracker.get_slot("tedavi_adi")
        yas = tracker.get_slot("yas")
        
        # Basit uyumluluk kontrolü
        warnings = []
        
        if hastalik:
            if "diabetes" in str(hastalik).lower() or "diyabet" in str(hastalik).lower():
                warnings.append("⚠️ Diyabet hastalarında özel tedavi protokolü uygulanır.")
            
            if "hypertension" in str(hastalik).lower() or "hipertansiyon" in str(hastalik).lower():
                warnings.append("⚠️ Tansiyon takibi ameliyat sürecinde yapılacaktır.")
        
        if yas:
            try:
                age = int(yas)
                if age > 70:
                    warnings.append("ℹ️ Yaşınız nedeniyle ek sağlık kontrolleri gerekebilir.")
            except:
                pass
        
        if warnings:
            message = "🏥 **Sağlık Durumu Bildirimi:**\n\n"
            message += "\n".join(warnings)
            message += "\n\nDoktorlarımız sizinle görüşme sonrası en uygun tedavi planını belirleyecektir."
            dispatcher.utter_message(text=message)
        
        return []


class ActionGenerateReport(Action):
    """Raporlama sistemi - Paydaşlar için"""
    
    def name(self) -> Text:
        return "action_generate_report"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Bu action genellikle admin/paydaş panelinden çağrılır
        # Örnek rapor türleri:
        # 1. Hasta sayısı ve demografik analiz
        # 2. Popüler tedavi türleri
        # 3. Klinik performans skorları
        # 4. Gelir analizi
        # 5. Müşteri memnuniyet skorları
        
        return []


class ActionDefaultFallback(Action):
    """
    Default fallback action - Rasa anlayamadığında çalışır
    """
    
    def name(self) -> Text:
        return "action_default_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        logger.info(f"🤷 Default fallback triggered: '{user_message}'")
        
        # Kullanıcıya yardımcı mesaj göster
        message = "Üzgünüm, tam olarak anlayamadım. 🤔\n\n"
        message += "✨ Şunları deneyebilirsiniz:\n"
        message += "• 'Antalya'da diş kliniği'\n"
        message += "• 'İstanbul'da rinoplasti'\n"
        message += "• 'Otel önerisi'\n"
        message += "• 'Fiyat bilgisi'\n\n"
        message += "Ya da bana doğrudan sorunuzu yazabilirsiniz."
        
        dispatcher.utter_message(text=message)
        
        return []
