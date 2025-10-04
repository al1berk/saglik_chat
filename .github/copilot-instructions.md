# GitHub Copilot Instructions - Sağlık Chat Projesi

## Proje Hakkında
Bu proje, **çok dilli medikal turizm** için akıllı klinik ve otel öneri sistemidir. 
- **6 Dil Desteği**: 🇹🇷 Turkish, 🇬🇧 English, 🇩🇪 German, 🇸🇦 Arabic, 🇷🇺 Russian, 🇳🇱 Dutch
- Klinik verileri (154 klinik)
- Otel verileri (5 otel)
- ChromaDB ile vektör arama
- Rasa ile NLU/Intent/NER (çok dilli)
- Ollama ile yerel LLM (çok dilli yanıtlar)

## Mimari
```
Kullanıcı (6 dilde) → Frontend (HTML/JS) 
         ↓
    API Service (FastAPI)
         ↓
    ├── Rasa Service (NLU/Intent/NER) - Dil algılama
    ├── ChromaDB (Vector Search)
    └── Ollama (LLM - Çok dilli açıklama/öneri)
```

## Veri Modeli

### Clinic Schema
```json
{
  "id": "ant_clinic_001",
  "name": "Klinik Adı",
  "rating": 4.65,
  "address": "Tam adres",
  "phone": "0 242 324 98 98",
  "city": "Antalya",
  "treatments": ["Composite Bonding", "Zirconium Crowns"]
}
```

### Hotel Schema
```json
{
  "id": "hotel_001",
  "name": "Otel Adı",
  "city": "Antalya",
  "country": "Turkey",
  "rating": 4.5,
  "price_per_night": 120,
  "features": ["Spa", "Pool"],
  "amenities": ["WiFi", "Restaurant"]
}
```

## Intent'ler (Rasa)
1. **search_clinic** - Klinik arama
   - Entities: city, treatment, rating
2. **search_hotel** - Otel arama
   - Entities: city, price_range
3. **ask_recommendation** - Öneri isteme
4. **ask_info** - Bilgi sorma
5. **greet** / **goodbye** - Selamlama
6. **detect_language** - Dil algılama (6 dil)

## Kod Kuralları

### Python
- Type hints kullan
- Async/await kullan (FastAPI için)
- Docstring'ler ekle
- Error handling yap
- Logging kullan
- **Çok dilli destek** için response'ları kullanıcı diline göre formatla

### API Endpoints
```python
POST /api/chat  # language parameter ekle
POST /api/search/clinics
POST /api/search/hotels
GET /api/clinics/{id}
GET /api/languages  # Desteklenen diller
GET /api/hotels/{id}
```

### ChromaDB Kullanımı
- Collection: "medical_clinics" ve "medical_hotels"
- Metadata filtreleme kullan: city, rating
- Similarity search ile en yakın 5 sonuç

### Rasa Kullanımı
- Intent confidence > 0.7 için güvenilir kabul et
- Entity extraction'dan city, treatment çıkar
- Fallback action'ları tanımla

### Ollama Kullanımı
- Model: "llama3"
- Temperature: 0.7
- Context window: 8192 tokens
- System prompt ile **çok dilli** cevap ver (6 dil desteği)
- Kullanıcı dilini algıla ve aynı dilde yanıt ver

## Dosya Yapısı
```
api_service/
  ├── app/
  │   ├── api/
  │   │   ├── endpoints/
  │   │   │   ├── chat.py      # Chat endpoint
  │   │   │   ├── clinics.py   # Klinik endpoints
  │   │   │   └── hotels.py    # Otel endpoints
  │   ├── core/
  │   │   ├── config.py        # Ayarlar
  │   │   └── ollama.py        # Ollama client
  │   └── services/
  │       ├── rasa_service.py  # Rasa integration
  │       └── search_service.py # ChromaDB search
  
rasa_service/
  ├── data/
  │   ├── nlu.yml             # Training data
  │   └── stories.yml         # Conversation flows
  ├── actions/
  │   └── actions.py          # Custom actions
  └── config.yml              # Rasa config
```

## Önemli Notlar
- Tüm cevaplar Türkçe olmalı
- Kullanıcı hiçbir teknik detay bilmiyor - basit kod örnekleri ver
- Hata mesajları kullanıcı dostu olmalı
- Veritabanı güncellemelerinde mevcut veriyi silme
- ChromaDB metadata'da None değer olmamalı
