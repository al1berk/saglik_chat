#!/usr/bin/env python3
"""
ChromaDB Veritabanı Hazırlama Script'i
Bu script clinics.json ve hotels.json dosyalarını okuyup ChromaDB'ye yükler
"""

import chromadb
import json
import os
from pathlib import Path

# Dizinleri ayarla
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STORAGE_DIR = PROJECT_ROOT / "storage" / "chroma_db"

# JSON dosyaları
CLINICS_JSON = RAW_DATA_DIR / "clinics.json"
HOTELS_JSON = RAW_DATA_DIR / "hotels.json"

# ChromaDB ayarları
CLINICS_COLLECTION = "medical_clinics"
HOTELS_COLLECTION = "medical_hotels"

def load_json_file(file_path):
    """JSON dosyasını yükle"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Eğer data bir dict ise ve içinde array varsa, onu al
        if isinstance(data, dict):
            # all_clinics veya clinics key'lerini dene
            if "all_clinics" in data:
                data = data["all_clinics"]
            elif "clinics" in data:
                data = data["clinics"]
            elif "hotels" in data:
                data = data["hotels"]
            # Eğer hiçbiri yoksa ve sadece 1 key varsa, onu al
            elif len(data) == 1:
                data = list(data.values())[0]
        
        print(f"✅ {file_path.name} dosyası okundu: {len(data)} kayıt")
        return data
    except FileNotFoundError:
        print(f"❌ HATA: {file_path} dosyası bulunamadı!")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON HATASI: {file_path} - {e}")
        return []

def prepare_clinic_data(clinics):
    """Klinik verilerini ChromaDB formatına dönüştür"""
    documents = []
    metadatas = []
    ids = []
    
    for clinic in clinics:
        # Şehir bilgisini al - önce city alanından, yoksa address'ten çıkar
        address = clinic.get("address", "")
        city = clinic.get("city", "")
        
        # Eğer city yok ama address varsa, address'ten çıkarmaya çalış
        if not city and address:
            # Son kısım genelde şehir/ilçe içerir (örn: "Muratpaşa/Antalya" veya "İstanbul")
            if "/" in address:
                # "/" sonrası şehir adı
                city = address.split("/")[-1].strip()
            elif "," in address:
                # "," sonrası şehir olabilir
                city = address.split(",")[-1].strip()
            else:
                # Boşluklarla ayrılmışsa son kelimeyi kontrol et
                words = address.strip().split()
                # Son kelime şehir olabilir (Antalya, İstanbul vb)
                if words:
                    last_word = words[-1].strip()
                    # Sayı veya kısa değilse muhtemelen şehir
                    if not last_word.isdigit() and len(last_word) > 3:
                        city = last_word
        
        # Hala yoksa varsayılan
        if not city:
            city = "Belirtilmemiş"
        
        # Zengin document metni oluştur
        treatments = ", ".join(clinic.get("treatments", []))
        specialties = ", ".join(clinic.get("specialties", []))
        features = ", ".join(clinic.get("features", []))
        
        document = (
            f"Klinik: {clinic.get('name', 'Bilinmiyor')}. "
            f"Şehir: {city}. "
            f"Ülke: Turkey. "
            f"Adres: {address}. "
            f"Tedaviler: {treatments}. "
            f"Uzmanlık: {specialties}. "
            f"Özellikler: {features}. "
            f"Telefon: {clinic.get('phone', '')}. "
            f"Açıklama: {clinic.get('description', '')}"
        )
        documents.append(document)
        
        # Metadata
        metadatas.append({
            "name": clinic.get("name", "Bilinmiyor"),
            "city": city,
            "country": "Turkey",
            "rating": float(clinic.get("rating", 0)),
            "price_range": clinic.get("price_range", "$$-$$$"),
            "treatments": treatments,
            "address": address,
            "phone": clinic.get("phone", ""),
            "type": "clinic"
        })
        
        # ID
        ids.append(clinic.get("id", f"clinic_{len(ids)}"))
    
    return documents, metadatas, ids

def prepare_hotel_data(hotels):
    """Otel verilerini ChromaDB formatına dönüştür"""
    documents = []
    metadatas = []
    ids = []
    
    for hotel in hotels:
        # Zengin document metni oluştur
        features = ", ".join(hotel.get("features", []))
        amenities = ", ".join(hotel.get("amenities", []))
        nearby = ", ".join(hotel.get("nearby_hospitals", []))
        
        document = (
            f"Otel: {hotel.get('name', 'Bilinmiyor')}. "
            f"Şehir: {hotel.get('city', 'Belirtilmemiş')}. "
            f"Ülke: {hotel.get('country', 'Turkey')}. "
            f"Tip: {hotel.get('type', 'Hotel')}. "
            f"Özellikler: {features}. "
            f"Olanaklar: {amenities}. "
            f"Yakın Hastaneler: {nearby}. "
            f"Açıklama: {hotel.get('description', '')}"
        )
        documents.append(document)
        
        # Metadata
        metadatas.append({
            "name": hotel.get("name", "Bilinmiyor"),
            "city": hotel.get("city", "Belirtilmemiş"),
            "country": hotel.get("country", "Turkey"),
            "hotel_type": hotel.get("type", "Hotel"),
            "rating": float(hotel.get("rating", 0)),
            "price_per_night": float(hotel.get("price_per_night", 0)),
            "type": "hotel"
        })
        
        # ID
        ids.append(hotel.get("id", f"hotel_{len(ids)}"))
    
    return documents, metadatas, ids

def add_to_collection(collection, documents, metadatas, ids, name):
    """Verileri koleksiyona ekle"""
    if not documents:
        print(f"⚠️  {name} için eklenecek veri yok")
        return
    
    # Mevcut ID'leri kontrol et
    try:
        existing = collection.get(ids=ids)
        existing_ids = set(existing['ids'])
    except:
        existing_ids = set()
    
    # Yeni kayıtları filtrele
    new_indices = [i for i, doc_id in enumerate(ids) if doc_id not in existing_ids]
    
    if new_indices:
        print(f"📥 {name}: {len(new_indices)} yeni kayıt ekleniyor...")
        collection.add(
            documents=[documents[i] for i in new_indices],
            metadatas=[metadatas[i] for i in new_indices],
            ids=[ids[i] for i in new_indices]
        )
        print(f"✅ {name}: Ekleme tamamlandı!")
    else:
        print(f"ℹ️  {name}: Tüm kayıtlar zaten mevcut")
    
    print(f"📊 {name} toplam kayıt sayısı: {collection.count()}")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🏥 ChromaDB Medikal Turizm Veritabanı Hazırlama")
    print("=" * 60)
    
    # Dizinleri oluştur
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Storage dizini: {STORAGE_DIR}")
    
    # ChromaDB client başlat
    print(f"🔧 ChromaDB başlatılıyor...")
    client = chromadb.PersistentClient(path=str(STORAGE_DIR))
    
    # Koleksiyonları oluştur
    print(f"📚 Koleksiyonlar oluşturuluyor...")
    clinics_collection = client.get_or_create_collection(
        name=CLINICS_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    hotels_collection = client.get_or_create_collection(
        name=HOTELS_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    
    # KLİNİKLERİ İŞLE
    print("\n" + "=" * 60)
    print("🏥 KLİNİKLER İŞLENİYOR")
    print("=" * 60)
    clinics = load_json_file(CLINICS_JSON)
    if clinics:
        docs, metas, ids = prepare_clinic_data(clinics)
        add_to_collection(clinics_collection, docs, metas, ids, "Klinikler")
    
    # OTELLERİ İŞLE
    print("\n" + "=" * 60)
    print("🏨 OTELLER İŞLENİYOR")
    print("=" * 60)
    hotels = load_json_file(HOTELS_JSON)
    if hotels:
        docs, metas, ids = prepare_hotel_data(hotels)
        add_to_collection(hotels_collection, docs, metas, ids, "Oteller")
    
    print("\n" + "=" * 60)
    print("✅ VERİTABANI HAZIR!")
    print("=" * 60)
    print(f"📊 Toplam Klinik: {clinics_collection.count()}")
    print(f"📊 Toplam Otel: {hotels_collection.count()}")
    print(f"📁 Veritabanı konumu: {STORAGE_DIR}")
    print("\n💡 Web viewer ile görüntülemek için:")
    print("   python scripts/web_viewer.py")

if __name__ == "__main__":
    main()