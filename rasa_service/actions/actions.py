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



class ActionAskOllama(Action):
    """Genel sorular için Ollama'ya sor - Rasa'nın anlayamadığı sorular buraya yönlendirilir"""
    
    def name(self) -> Text:
        return "action_ask_ollama"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get('text', '')
        logger.info(f"🤖 Ollama'ya genel soru (fallback): '{user_message}'")

        # Slot'tan context bilgisi al
        tedavi = tracker.get_slot("tedavi")
        sehir = tracker.get_slot("sehir")
        
        # Context'i prompt'a ekle
        context_info = ""
        if tedavi:
            context_info += f"\nKullanıcı daha önce '{tedavi}' tedavisi hakkında sordu."
        if sehir:
            context_info += f"\nKullanıcı '{sehir}' şehrinde arama yapıyor."

        prompt = f"""Sen profesyonel bir Türk sağlık turizmi danışmanısın. Türkiye'deki medikal turizm konusunda uzmansın.

GÖREVIN: Kullanıcının sorusunu sağlık turizmi perspektifinden yanıtla. 

ÖNEMLİ KURALLAR:
1. SADECE TÜRKÇE CEVAP VER
2. Kısa, net ve profesyonel ol (maksimum 4-5 cümle)
3. Eğer medikal bir soru ise, genel bilgi ver (kesin tanı/tedavi önerme)
4. Fiyat soruluyorsa, genel aralık ver
5. Klinik/otel önerisi isteniyorsa, kriterleri sor

CONTEXT:{context_info}

KULLANICI SORUSU: {user_message}

TÜRKÇE CEVAP:"""
        
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,  # Daha tutarlı cevaplar
                "num_predict": 400,  # Biraz daha uzun cevaplar
                "top_p": 0.9,
                "repeat_penalty": 1.3,
                "stop": ["KULLANICI", "USER:", "English:", "In English:"]
            }
        }

        dispatcher.utter_message(text="🤔 Düşünüyorum...")

        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=OLLAMA_TIMEOUT, proxies=PROXIES)
            response.raise_for_status()
            
            generated_text = response.json().get('response', '').strip()

            if generated_text:
                dispatcher.utter_message(text=f"💡 {generated_text}")
                logger.info(f"✅ Ollama fallback cevabı: {len(generated_text)} karakter")
            else:
                dispatcher.utter_message(text="Üzgünüm, bu soruya şu anda cevap veremiyorum. Daha spesifik sorular sorabilirsiniz:\n- Klinik aramak için: 'Antalya'da saç ekimi kliniği'\n- Otel aramak için: 'İstanbul'da otel'\n- Tedavi bilgisi için: 'Rinoplasti nedir?'")

        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama servisine bağlanılamadı")
            dispatcher.utter_message(text="❌ Yapay zeka servisi çalışmıyor. Lütfen spesifik sorular sorun:\n- Klinik arama\n- Otel arama\n- Tedavi bilgisi")
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Ollama timeout ({OLLAMA_TIMEOUT}s)")
            dispatcher.utter_message(text="⏱️ Cevap hazırlanırken zaman aşımı. Lütfen tekrar deneyin.")
        except Exception as e:
            logger.error(f"❌ Ollama hatası: {e}")
            dispatcher.utter_message(text="Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.")

        return []









# ============ KLİNİK VERİTABANI (Örnek) ============
CLINICS_DB = {
    "dental": {
        "Antalya": [
            {
                "name": "Antmodern Oral & Dental Health Clinic",
                "address": "Fener Mah. Bülent Ecevit Blv. No:50 Muratpaşa/Antalya",
                "district": "Muratpaşa",
                "treatments": ["Composite Bonding", "Porcelain Veneers", "Teeth Whitening", 
                              "Orthodontics", "Implant Dentistry", "Zirconium Crowns"],
                "rating": 4.8,
                "accreditations": ["JCI", "ISO 9001"],
                "languages": ["Turkish", "English", "Russian", "Arabic"]
            },
            {
                "name": "Dt. Murat Özbıyık Clinic",
                "address": "Yeşilbahçe Mah. Metin Kasapoğlu Cad. 3/1 Muratpaşa/Antalya",
                "district": "Muratpaşa",
                "treatments": ["Root Canal Treatment", "Dental Implants", "Smile Restoration", 
                              "Invisalign", "Bone Graft"],
                "rating": 4.7,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English", "German"]
            },
            {
                "name": "Markasya Oral & Dental Health Clinic",
                "address": "Toros Mah. 805 Sok. Kurgu Plaza No: 14/1 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Cosmetic Dentistry", "Periodontics", "Gum Disease Treatment", 
                              "Dentures", "Sedation"],
                "rating": 4.6,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English"]
            }
        ]
    },
    "aesthetic": {
        "Antalya": [
            {
                "name": "Dr. Gökhan Özerdem Clinic",
                "address": "Yeşilbahçe Mah. Metin Kasapoğlu Cad. Ayhan Kadam İş Merkezi A blok No: 48/11 Muratpaşa/Antalya",
                "district": "Muratpaşa",
                "treatments": ["Rhinoplasty", "Botox", "Face Lift", "Breast Surgery", 
                              "Liposuction", "Genioplasty"],
                "rating": 4.9,
                "accreditations": ["JCI", "ISO 9001", "ISAPS"],
                "languages": ["Turkish", "English", "Arabic", "Russian"]
            },
            {
                "name": "Dr. Hasan Hüseyin Balıkçı Clinic",
                "address": "Arapsuyu Mah. Atatürk Bulvarı M. Gökay Plaza No:23/41 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Septoplasty", "Chin Filler", "Eye Contour Aesthetics", 
                              "Lip Lift", "Cheek Augmentation"],
                "rating": 4.8,
                "accreditations": ["ISO 9001", "TSAPS"],
                "languages": ["Turkish", "English", "German"]
            }
        ]
    },
    "eye_care": {
        "Antalya": [
            {
                "name": "Akdeniz Hospital",
                "address": "Sorgun Mah. 8151 Sk.No:10 Manavgat/Antalya",
                "district": "Manavgat",
                "treatments": ["Cataract", "Glaucoma", "Retinal Diseases", 
                              "Intraocular Lens Implants", "Keratoplasty"],
                "rating": 4.7,
                "accreditations": ["JCI", "ISO 9001"],
                "languages": ["Turkish", "English", "Russian"]
            },
            {
                "name": "Akdeniz Şifa Konyaaltı Medical Center",
                "address": "Kuşkavağı Mah. Atatürk Bulvarı No:81 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Cataract", "Lazy Eye", "Oculoplastic Surgery", 
                              "Extracapsular Cataract Extraction"],
                "rating": 4.6,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English"]
            }
        ]
    }
}

# ============ OTEL VERİTABANI (Örnek) ============
HOTELS_DB = {
    "Belek": [
        {"name": "Regnum Carya Golf & Spa Resort", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Golf"], "price_range": "premium"},
        {"name": "Rixos Premium Belek", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Beach"], "price_range": "premium"},
        {"name": "Maxx Royal Belek Golf Resort", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Golf"], "price_range": "luxury"}
    ],
    "Lara": [
        {"name": "Delphin Palace", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Beach"], "price_range": "premium"},
        {"name": "Titanic Beach Lara", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Aquapark"], "price_range": "premium"},
        {"name": "Rixos Premium Belek", "stars": 5, "features": ["Spa", "Pool", "All Inclusive"], "price_range": "luxury"}
    ],
    "Side": [
        {"name": "Barut Hotels Hemera", "stars": 5, "features": ["Spa", "Pool", "All Inclusive"], "price_range": "standard"},
        {"name": "Royal Dragon Hotel", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Aquapark"], "price_range": "premium"}
    ],
    "Alanya": [
        {"name": "Eftalia Ocean Hotel", "stars": 5, "features": ["Spa", "Pool", "All Inclusive"], "price_range": "standard"},
        {"name": "Granada Luxury Resort", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Beach"], "price_range": "premium"}
    ],
    "Kemer": [
        {"name": "Rixos Sungate", "stars": 5, "features": ["Spa", "Pool", "All Inclusive", "Beach"], "price_range": "premium"},
        {"name": "Crystal Sunrise Queen Luxury Resort", "stars": 5, "features": ["Spa", "Pool", "All Inclusive"], "price_range": "premium"}
    ],
    "Konyaaltı": [
        {"name": "Sheraton Voyager Antalya", "stars": 5, "features": ["Spa", "Pool", "Beach", "City Center"], "price_range": "premium"},
        {"name": "DoubleTree by Hilton Antalya", "stars": 4, "features": ["Pool", "Beach", "City Center"], "price_range": "standard"}
    ]
}



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
    """Tedavi türüne göre klinik ara"""
    
    def name(self) -> Text:
        return "action_search_clinics_by_treatment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        tedavi_adi = tracker.get_slot("tedavi_adi")
        tedavi_turu = tracker.get_slot("tedavi_turu")
        sehir = tracker.get_slot("sehir")
        
        # Tedavi türünü belirle
        if not tedavi_turu:
            if tedavi_adi:
                # Tedavi adından türü çıkar
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
        
        # API çağrısı simülasyonu - gerçek uygulamada API kullanılacak
        if tedavi_turu and sehir:
            clinics = CLINICS_DB.get(tedavi_turu, {}).get(sehir, [])
            
            if clinics:
                message = f"✅ {sehir} için {len(clinics)} klinik bulundu!\n\n"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text=f"Üzgünüm, {sehir}'da bu tedavi için klinik bulunamadı.")
        
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
    """Bölgeye göre otel ara"""
    
    def name(self) -> Text:
        return "action_search_hotels_by_region"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        bolge = tracker.get_slot("bolge")
        otel_kategori = tracker.get_slot("otel_kategori")
        
        if bolge and bolge in HOTELS_DB:
            hotels = HOTELS_DB[bolge]
            
            # Kategori filtrele
            if otel_kategori:
                stars = 5 if "5" in otel_kategori else 4
                hotels = [h for h in hotels if h["stars"] == stars]
            
            message = f"🏨 {bolge} bölgesinde {len(hotels)} otel bulundu!"
            dispatcher.utter_message(text=message)
        
        return []


class ActionGenerateBundleRecommendation(Action):
    """Yapay zeka destekli paket önerisi oluştur"""
    
    def name(self) -> Text:
        return "action_generate_bundle_recommendation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Kullanıcı bilgilerini topla
        user_profile = {
            "tedavi_turu": tracker.get_slot("tedavi_turu"),
            "tedavi_adi": tracker.get_slot("tedavi_adi"),
            "sehir": tracker.get_slot("sehir"),
            "bolge": tracker.get_slot("bolge"),
            "tarih": tracker.get_slot("tarih"),
            "butce": tracker.get_slot("butce"),
            "otel_kategori": tracker.get_slot("otel_kategori"),
            "ucus_sinifi": tracker.get_slot("ucus_sinifi"),
            "ucus_tipi": tracker.get_slot("ucus_tipi")
        }
        
        # Recommendation Engine çağrısı simülasyonu
        # Gerçek uygulamada ML modeli ve API kullanılacak
        
        bundles = []
        tedavi_turu = user_profile.get("tedavi_turu", "dental")
        sehir = user_profile.get("sehir", "Antalya")
        bolge = user_profile.get("bolge", "Lara")
        
        # Örnek klinikler
        clinics = CLINICS_DB.get(tedavi_turu, {}).get(sehir, [])[:3]
        
        # Örnek oteller
        hotels = HOTELS_DB.get(bolge, HOTELS_DB["Lara"])[:3]
        
        # 3 farklı paket oluştur
        for i in range(min(3, len(clinics))):
            clinic = clinics[i] if i < len(clinics) else clinics[0]
            hotel = hotels[i] if i < len(hotels) else hotels[0]
            
            # Fiyat hesapla
            treatment_price = calculate_treatment_price(
                user_profile.get("tedavi_adi", "dental treatment"),
                clinic.get("rating", 4.5)
            )
            hotel_price = calculate_hotel_price(hotel, nights=7)
            flight_price = calculate_flight_price(
                user_profile.get("ucus_sinifi", "economy"),
                user_profile.get("ucus_tipi", "connecting")
            )
            transfer_price = 150
            
            total_price = treatment_price + hotel_price + (flight_price * 2) + transfer_price
            
            bundles.append({
                "name": f"Paket {i+1} - {['Ekonomik', 'Standart', 'Premium'][i]}",
                "clinic": clinic["name"],
                "clinic_rating": clinic["rating"],
                "hotel": hotel["name"],
                "hotel_stars": hotel["stars"],
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
    """Klinik detaylarını göster"""
    
    def name(self) -> Text:
        return "action_provide_clinic_details"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        klinik_adi = tracker.get_slot("klinik_adi")
        
        if klinik_adi:
            # Klinik bilgisini bul
            clinic_found = None
            for category in CLINICS_DB.values():
                for city_clinics in category.values():
                    for clinic in city_clinics:
                        if clinic["name"] == klinik_adi:
                            clinic_found = clinic
                            break
            
            if clinic_found:
                message = f"🏥 **{clinic_found['name']}**\n\n"
                message += f"📍 Adres: {clinic_found['address']}\n"
                message += f"⭐ Rating: {clinic_found['rating']}/5.0\n"
                message += f"🏆 Akreditasyonlar: {', '.join(clinic_found['accreditations'])}\n"
                message += f"🌍 Diller: {', '.join(clinic_found['languages'])}\n\n"
                message += f"💉 Tedaviler:\n"
                for treatment in clinic_found['treatments'][:5]:
                    message += f"• {treatment}\n"
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text=f"Üzgünüm, {klinik_adi} hakkında detaylı bilgi bulunamadı.")
        
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
