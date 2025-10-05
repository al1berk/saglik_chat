"""
ChromaDB Arama Servisi
Klinik ve otel verilerinde METADATA-ONLY arama yapar (embedding yok - ultra hızlı)
"""
import chromadb
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
import time

logger = logging.getLogger(__name__)

# Basit cache sistemi
_cache = {}
_cache_ttl = 60  # 60 saniye cache

def _get_cache_key(collection_name: str, filters: dict) -> str:
    """Cache anahtarı oluştur"""
    return f"{collection_name}:{str(filters)}"

def _get_from_cache(key: str) -> Optional[List[Dict]]:
    """Cache'den veri çek"""
    if key in _cache:
        data, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            logger.info(f"📦 Cache hit: {key}")
            return data
    return None

def _save_to_cache(key: str, data: List[Dict]):
    """Cache'e kaydet"""
    _cache[key] = (data, time.time())

class SearchService:
    """ChromaDB ile arama servisi (Metadata-only - ultra hızlı)"""
    
    def __init__(self):
        """ChromaDB bağlantısını başlat"""
        try:
            # Performans için Settings
            chroma_settings = chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
            
            self.client = chromadb.PersistentClient(
                path=str(settings.CHROMA_DB_PATH),
                settings=chroma_settings
            )
            self.clinics_collection = self.client.get_collection(name=settings.CLINICS_COLLECTION)
            self.hotels_collection = self.client.get_collection(name=settings.HOTELS_COLLECTION)
            logger.info(f"✅ ChromaDB bağlantısı başarılı: {settings.CHROMA_DB_PATH}")
            logger.info(f"📊 Toplam klinik: {self.clinics_collection.count()}")
            logger.info(f"📊 Toplam otel: {self.hotels_collection.count()}")
        except Exception as e:
            logger.error(f"❌ ChromaDB bağlantı hatası: {e}")
            raise
    
    def search_clinics(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        treatment: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Klinik ara (METADATA-ONLY - embedding yok, ultra hızlı)
        """
        start_time = time.time()
        
        # Cache kontrol et
        cache_key = _get_cache_key("clinics", {"city": city, "treatment": treatment})
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            return cached_result[:limit]
        
        try:
            logger.info(f"🔍 Klinik arama başladı: city={city}, treatment={treatment}")
            
            # METADATA-ONLY GET (embedding hesaplama yok!)
            where_filter = {}
            if city:
                where_filter["city"] = city
            
            # Tüm klinikleri çek (metadata filtresi ile)
            if where_filter:
                results = self.clinics_collection.get(
                    where=where_filter,
                    limit=100  # Maksimum 100 klinik
                )
            else:
                results = self.clinics_collection.get(
                    limit=100
                )
            
            # Sonuçları formatla ve filtrele
            clinics = []
            if results and results.get('metadatas'):
                for i, metadata in enumerate(results['metadatas']):
                    clinic = {
                        "id": results['ids'][i],
                        "name": metadata.get("name", ""),
                        "city": metadata.get("city", ""),
                        "rating": float(metadata.get("rating", 0)),
                        "phone": metadata.get("phone", ""),
                        "address": metadata.get("address", ""),
                        "treatments": metadata.get("treatments", "").split(",") if metadata.get("treatments") else []
                    }
                    
                    # Tedavi filtresi uygula (text search)
                    if treatment:
                        treatments_lower = [t.lower().strip() for t in clinic["treatments"]]
                        if not any(treatment.lower() in t for t in treatments_lower):
                            continue
                    
                    # Rating filtresi uygula
                    if min_rating and clinic["rating"] < min_rating:
                        continue
                    
                    clinics.append(clinic)
                    
                    if len(clinics) >= limit:
                        break
            
            # Rating'e göre sırala (en yüksek önce)
            clinics.sort(key=lambda x: x["rating"], reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ {len(clinics)} klinik bulundu ({elapsed:.2f}s)")
            
            # Cache'e kaydet
            _save_to_cache(cache_key, clinics)
            
            return clinics[:limit]
            
        except Exception as e:
            logger.error(f"❌ Klinik arama hatası: {e}")
            return []
    
    def search_hotels(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        hotel_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Otel ara (METADATA-ONLY - embedding yok, ultra hızlı)
        """
        start_time = time.time()
        
        # Cache kontrol et
        cache_key = _get_cache_key("hotels", {"city": city, "type": hotel_type})
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            return cached_result[:limit]
        
        try:
            logger.info(f"🔍 Otel arama başladı: city={city}")
            
            # METADATA-ONLY GET (embedding hesaplama yok!)
            where_filter = {}
            if city:
                where_filter["city"] = city
            
            # Tüm otelleri çek (metadata filtresi ile)
            if where_filter:
                results = self.hotels_collection.get(
                    where=where_filter,
                    limit=100
                )
            else:
                results = self.hotels_collection.get(
                    limit=100
                )
            
            # Sonuçları formatla ve filtrele
            hotels = []
            if results and results.get('metadatas'):
                for i, metadata in enumerate(results['metadatas']):
                    hotel = {
                        "id": results['ids'][i],
                        "name": metadata.get("name", ""),
                        "city": metadata.get("city", ""),
                        "country": metadata.get("country", "Turkey"),
                        "type": metadata.get("type", ""),
                        "rating": float(metadata.get("rating", 0)),
                        "price_per_night": float(metadata.get("price_per_night", 0)),
                        "description": metadata.get("description", ""),
                        "features": metadata.get("features", "").split(",") if metadata.get("features") else [],
                        "amenities": metadata.get("amenities", "").split(",") if metadata.get("amenities") else []
                    }
                    
                    # Rating filtresi
                    if min_rating and hotel["rating"] < min_rating:
                        continue
                    
                    # Fiyat filtresi
                    if max_price and hotel["price_per_night"] > max_price:
                        continue
                    
                    hotels.append(hotel)
                    
                    if len(hotels) >= limit * 2:  # Biraz fazla al, filtrelemeden sonra yeterli olsun
                        break
            
            # Rating'e göre sırala (en yüksek önce)
            hotels.sort(key=lambda x: x["rating"], reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ {len(hotels)} otel bulundu ({elapsed:.2f}s)")
            
            # Cache'e kaydet
            _save_to_cache(cache_key, hotels)
            
            return hotels[:limit]
            
        except Exception as e:
            logger.error(f"❌ Otel arama hatası: {e}")
            return []
    
    def get_clinic_by_id(self, clinic_id: str) -> Optional[Dict[str, Any]]:
        """ID ile klinik getir"""
        try:
            result = self.clinics_collection.get(ids=[clinic_id])
            
            if result and result.get('metadatas'):
                metadata = result['metadatas'][0]
                return {
                    "id": clinic_id,
                    "name": metadata.get("name", ""),
                    "city": metadata.get("city", ""),
                    "rating": float(metadata.get("rating", 0)),
                    "phone": metadata.get("phone", ""),
                    "address": metadata.get("address", ""),
                    "treatments": metadata.get("treatments", "").split(",") if metadata.get("treatments") else []
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Klinik getirme hatası: {e}")
            return None
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """ID ile otel getir"""
        try:
            result = self.hotels_collection.get(ids=[hotel_id])
            
            if result and result.get('metadatas'):
                metadata = result['metadatas'][0]
                return {
                    "id": hotel_id,
                    "name": metadata.get("name", ""),
                    "city": metadata.get("city", ""),
                    "country": metadata.get("country", "Turkey"),
                    "type": metadata.get("type", ""),
                    "rating": float(metadata.get("rating", 0)),
                    "price_per_night": float(metadata.get("price_per_night", 0)),
                    "description": metadata.get("description", ""),
                    "features": metadata.get("features", "").split(",") if metadata.get("features") else [],
                    "amenities": metadata.get("amenities", "").split(",") if metadata.get("amenities") else []
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Otel getirme hatası: {e}")
            return None

# Global instance
search_service = SearchService()
