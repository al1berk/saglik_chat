# actions/api_clients.py
"""
API Client Layer - Mock ve Real API arasında geçiş yapabilir
"""

import httpx
import os
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================
USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() == "true"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

# Real API Endpoints
CLINIC_API_URL = os.getenv("CLINIC_API_URL", "")
CLINIC_API_KEY = os.getenv("CLINIC_API_KEY", "")

HOTEL_API_URL = os.getenv("HOTEL_API_URL", "")
HOTEL_API_KEY = os.getenv("HOTEL_API_KEY", "")

FLIGHT_API_URL = os.getenv("FLIGHT_API_URL", "")
FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY", "")


# ============================================
# MOCK DATA
# ============================================

# api_clients.py içinde

MOCK_CLINICS = {
    "dental": {
        "Antalya": [
            {
                "id": 1,
                "name": "Antmodern Oral & Dental Health Clinic",
                "address": "Fener Mah. Bülent Ecevit Blv. No:50 Muratpaşa/Antalya",
                "city": "Antalya",
                "district": "Muratpaşa",
                "treatments": ["Composite Bonding", "Porcelain Veneers", "Teeth Whitening", 
                              "Orthodontics", "Implant Dentistry", "Zirconium Crowns"],
                "rating": 4.8,
                "accreditations": ["JCI", "ISO 9001"],
                "languages": ["Turkish", "English", "Russian", "Arabic"],
                "price_range": "medium"
            },
            {
                "id": 2,
                "name": "Dt. Murat Özbıyık Clinic",
                "address": "Yeşilbahçe Mah. Metin Kasapoğlu Cad. 3/1 Muratpaşa/Antalya",
                "district": "Muratpaşa",
                "treatments": ["Root Canal Treatment", "Dental Implants", "Smile Restoration", 
                              "Invisalign", "Bone Graft"],
                "rating": 4.7,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English", "German"],
                "price_range": "medium"
            },
            {
                "id": 3,
                "name": "Markasya Oral & Dental Health Clinic",
                "address": "Toros Mah. 805 Sok. Kurgu Plaza No: 14/1 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Cosmetic Dentistry", "Periodontics", "Gum Disease Treatment", 
                              "Dentures", "Sedation"],
                "rating": 4.6,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English"],
                "price_range": "medium"
            }
        ]
    },
    "aesthetic": {
        "Antalya": [
            {
                "id": 4,
                "name": "Dr. Gökhan Özerdem Clinic",
                "address": "Yeşilbahçe Mah. Metin Kasapoğlu Cad. Ayhan Kadam İş Merkezi A blok No: 48/11 Muratpaşa/Antalya",
                "city": "Antalya",
                "district": "Muratpaşa",
                "treatments": ["Rhinoplasty", "Botox", "Face Lift", "Breast Surgery", 
                              "Liposuction", "Genioplasty"],
                "rating": 4.9,
                "accreditations": ["JCI", "ISO 9001", "ISAPS"],
                "languages": ["Turkish", "English", "Arabic", "Russian"],
                "price_range": "premium"
            },
            {
                "id": 5,
                "name": "Dr. Hasan Hüseyin Balıkçı Clinic",
                "address": "Arapsuyu Mah. Atatürk Bulvarı M. Gökay Plaza No:23/41 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Septoplasty", "Chin Filler", "Eye Contour Aesthetics", 
                              "Lip Lift", "Cheek Augmentation"],
                "rating": 4.8,
                "accreditations": ["ISO 9001", "TSAPS"],
                "languages": ["Turkish", "English", "German"],
                "price_range": "premium"
            }
        ]
    },
    "eye_care": {
        "Antalya": [
            {
                "id": 6,
                "name": "Akdeniz Hospital",
                "address": "Sorgun Mah. 8151 Sk.No:10 Manavgat/Antalya",
                "city": "Antalya",
                "district": "Manavgat",
                "treatments": ["Cataract", "Glaucoma", "Retinal Diseases", 
                              "Intraocular Lens Implants", "Keratoplasty"],
                "rating": 4.7,
                "accreditations": ["JCI", "ISO 9001"],
                "languages": ["Turkish", "English", "Russian"],
                "price_range": "medium"
            },
            {
                "id": 7,
                "name": "Akdeniz Şifa Konyaaltı Medical Center",
                "address": "Kuşkavağı Mah. Atatürk Bulvarı No:81 Konyaaltı/Antalya",
                "district": "Konyaaltı",
                "treatments": ["Cataract", "Lazy Eye", "Oculoplastic Surgery", 
                              "Extracapsular Cataract Extraction"],
                "rating": 4.6,
                "accreditations": ["ISO 9001"],
                "languages": ["Turkish", "English"],
                "price_range": "medium"
            }
        ]
    }
}

MOCK_HOTELS = {
    "Belek": [
        {
            "id": 1,
            "name": "Regnum Carya Golf & Spa Resort",
            "region": "Belek",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Golf"],
            "price_range": "premium",
            "price_per_night": 350
        },
        {
            "id": 2,
            "name": "Rixos Premium Belek",
            "region": "Belek",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Beach"],
            "price_range": "premium",
            "price_per_night": 320
        },
        {
            "id": 3,
            "name": "Maxx Royal Belek Golf Resort",
            "region": "Belek",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Golf"],
            "price_range": "luxury",
            "price_per_night": 450
        }
    ],
    "Lara": [
        {
            "id": 4,
            "name": "Delphin Palace",
            "region": "Lara",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Beach"],
            "price_range": "premium",
            "price_per_night": 200
        },
        {
            "id": 5,
            "name": "Titanic Beach Lara",
            "region": "Lara",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Aquapark"],
            "price_range": "premium",
            "price_per_night": 180
        }
    ],
    "Side": [
        {
            "id": 6,
            "name": "Barut Hotels Hemera",
            "region": "Side",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive"],
            "price_range": "standard",
            "price_per_night": 150
        },
        {
            "id": 7,
            "name": "Royal Dragon Hotel",
            "region": "Side",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Aquapark"],
            "price_range": "premium",
            "price_per_night": 200
        }
    ],
    "Alanya": [
        {
            "id": 8,
            "name": "Eftalia Ocean Hotel",
            "region": "Alanya",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive"],
            "price_range": "standard",
            "price_per_night": 120
        },
        {
            "id": 9,
            "name": "Granada Luxury Resort",
            "region": "Alanya",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Beach"],
            "price_range": "premium",
            "price_per_night": 180
        }
    ],
    "Kemer": [
        {
            "id": 10,
            "name": "Rixos Sungate",
            "region": "Kemer",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive", "Beach"],
            "price_range": "premium",
            "price_per_night": 250
        },
        {
            "id": 11,
            "name": "Crystal Sunrise Queen Luxury Resort",
            "region": "Kemer",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "All Inclusive"],
            "price_range": "premium",
            "price_per_night": 220
        }
    ],
    "Konyaaltı": [
        {
            "id": 12,
            "name": "Sheraton Voyager Antalya",
            "region": "Konyaaltı",
            "city": "Antalya",
            "stars": 5,
            "features": ["Spa", "Pool", "Beach", "City Center"],
            "price_range": "premium",
            "price_per_night": 220
        },
        {
            "id": 13,
            "name": "DoubleTree by Hilton Antalya",
            "region": "Konyaaltı",
            "city": "Antalya",
            "stars": 4,
            "features": ["Pool", "Beach", "City Center"],
            "price_range": "standard",
            "price_per_night": 150
        }
    ]
}

MOCK_FLIGHTS = [
    {
        "id": 1,
        "airline": "Turkish Airlines",
        "price": 280,
        "class": "economy",
        "type": "direct"
    }
]


# ============================================
# BASE API CLIENT
# ============================================

class BaseAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.use_mock = USE_MOCK_API
        
        if not self.use_mock and self.api_key:
            self.client = httpx.Client(
                timeout=API_TIMEOUT,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            logger.info(f"✅ Real API: {base_url}")
        else:
            logger.info("🎭 Mock API mode")


# ============================================
# CLINIC API CLIENT
# ============================================

class ClinicAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(CLINIC_API_URL, CLINIC_API_KEY)
    
    def search_clinics(self, treatment_type: str = None,city: str = None,treatment_name: str = None):
    
        if self.use_mock:
            return self._mock_search(treatment_type, city, treatment_name)
        else:
            return self._real_search(treatment_type, city, treatment_name)
    
    def _mock_search(self, treatment_type, city, treatment_name):
        results = []
        
        logger.info(f"🔍 Mock Search - treatment_type: {treatment_type}, city: {city}, treatment_name: {treatment_name}")
        
        # Şehir adını normalize et (case-insensitive)
        city_normalized = city.title() if city else None
        
        # Tedavi türüne göre filtrele
        if treatment_type and treatment_type in MOCK_CLINICS:
            category_clinics = MOCK_CLINICS[treatment_type]
            
            # Şehre göre filtrele
            if city_normalized and city_normalized in category_clinics:
                clinics = category_clinics[city_normalized]
                logger.info(f"✅ {len(clinics)} klinik bulundu (treatment_type: {treatment_type}, city: {city_normalized})")
            else:
                # Şehir belirtilmemiş veya bulunamadı, tüm şehirlerdeki klinikleri al
                clinics = []
                for city_clinics in category_clinics.values():
                    clinics.extend(city_clinics)
                logger.info(f"✅ Tüm şehirlerde {len(clinics)} klinik bulundu (treatment_type: {treatment_type})")
        else:
            # Tüm klinikleri al
            clinics = []
            for category in MOCK_CLINICS.values():
                for city_clinics in category.values():
                    clinics.extend(city_clinics)
            logger.info(f"✅ Tüm kategorilerde {len(clinics)} klinik bulundu")
        
        # Treatment name filtresi - Türkçe-İngilizce mapping
        treatment_mapping = {
            "diş implantı": ["implant", "dental implant"],
            "implant": ["implant", "dental implant"],
            "rinoplasti": ["rhinoplasty"],
            "burun estetiği": ["rhinoplasty"],
            "saç ekimi": ["hair transplant"],
            "göz ameliyatı": ["cataract", "laser eye"],
            "katarakt": ["cataract"],
            "botox": ["botox"],
            "dolgu": ["filler"]
        }
        
        if treatment_name:
            treatment_name_lower = treatment_name.lower()
            
            # Türkçe-İngilizce mapping'den eşleşme bul
            search_terms = treatment_mapping.get(treatment_name_lower, [treatment_name_lower])
            
            results = [
                c for c in clinics 
                if any(
                    any(term in t.lower() for term in search_terms)
                    for t in c["treatments"]
                )
            ]
            logger.info(f"✅ Treatment name filtresinden sonra {len(results)} klinik kaldı (search terms: {search_terms})")
        else:
            results = clinics
        
        logger.info(f"🎭 Mock: TOPLAM {len(results)} klinik bulundu")
        return {"total": len(results), "results": results}
    
    def _real_search(self, treatment, city):
        """Gerçek API çağrısı"""
        try:
            response = self.client.post(
                f"{self.base_url}/clinics/search",
                json={"treatment": treatment, "city": city}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ API Error: {e}")
            # Fallback to mock
            return self._mock_search(treatment, city)


# ============================================
# HOTEL API CLIENT
# ============================================

class HotelAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(HOTEL_API_URL, HOTEL_API_KEY)
    
    def search_hotels(self, region: str = None, stars: int = 4):
        if self.use_mock:
            return self._mock_search(region, stars)
        else:
            return self._real_search(region, stars)
    
    def _mock_search(self, region, stars):
        results = []
        
        if region and region in MOCK_HOTELS:
            hotels = MOCK_HOTELS[region]
        else:
            hotels = []
            for region_hotels in MOCK_HOTELS.values():
                hotels.extend(region_hotels)
        
        results = [h for h in hotels if h["stars"] >= stars]
        
        logger.info(f"🎭 Mock: {len(results)} otel bulundu")
        return {"total": len(results), "results": results}
    
    def _real_search(self, region, stars):
        try:
            response = self.client.post(
                f"{self.base_url}/hotels/search",
                json={"region": region, "stars": stars}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ API Error: {e}")
            return self._mock_search(region, stars)


# ============================================
# FLIGHT API CLIENT
# ============================================

class FlightAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(FLIGHT_API_URL, FLIGHT_API_KEY)
    
    def search_flights(self, flight_class: str = "economy"):
        if self.use_mock:
            return self._mock_search(flight_class)
        else:
            return self._real_search(flight_class)
    
    def _mock_search(self, flight_class):
        results = [f for f in MOCK_FLIGHTS if f["class"] == flight_class]
        logger.info(f"🎭 Mock: {len(results)} uçuş bulundu")
        return {"total": len(results), "results": results}
    
    def _real_search(self, flight_class):
        try:
            response = self.client.post(
                f"{self.base_url}/flights/search",
                json={"class": flight_class}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ API Error: {e}")
            return self._mock_search(flight_class)