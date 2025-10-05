# 🏥 Sağlık Chat API - Kullanım Kılavuzu

## 📋 Özet

Projenizde **ChromaDB entegrasyonu** ve **Ollama LLM servisi** artık tamamen entegre edildi!

### ✅ Eklenen Özellikler

1. **ChromaDB Arama Servisi** (`app/services/search_service.py`)
   - Klinik ve otel verilerinde vektör tabanlı arama
   - Şehir, tedavi, fiyat filtreleme
   - Similarity search ile en alakalı sonuçlar

2. **Ollama LLM Servisi** (`app/core/ollama.py`)
   - Doğal dil cevap üretimi
   - Klinik ve otel önerileri
   - Türkçe yanıt desteği

3. **Yeni API Endpoint'leri**
   - `GET /api/clinics/search` - Klinik ara (ChromaDB)
   - `GET /api/hotels/search` - Otel ara (ChromaDB)
   - `POST /api/chat` - Rasa ile chat
   - `POST /api/chat/smart` - Ollama ile direkt chat

---

## 🚀 Sistemi Başlatma

### 1. ChromaDB Hazırlama (İlk Defa)

```bash
cd api_service
python scripts/prepare_data.py
```

**Çıktı:**
```
✅ ChromaDB'ye 105 klinik eklendi
✅ ChromaDB'ye 5 otel eklendi
```

### 2. Ollama Başlatma

**Terminal 1:**
```bash
ollama serve
```

**Ollama modeli indir (ilk defa):**
```bash
ollama pull llama3
```

### 3. Rasa Başlatma (Opsiyonel)

**Terminal 2:**
```bash
cd rasa_service
rasa run --enable-api --port 5005
```

### 4. API Sunucusu Başlatma

**Terminal 3:**
```bash
cd api_service
python main.py
```

veya uvicorn ile:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Sistem Testleri

**Terminal 4:**
```bash
cd api_service
python scripts/test_services.py
```

Bu script tüm servisleri test eder ve hangi servisin çalışıp çalışmadığını gösterir.

---

## 📡 API Endpoint'leri

### 1. Klinik Arama (ChromaDB)

**Endpoint:** `GET /api/clinics/search`

**Parametreler:**
- `q` (opsiyonel): Arama metni
- `city` (opsiyonel): Şehir filtresi (örn: "Antalya", "İstanbul")
- `treatment` (opsiyonel): Tedavi türü (örn: "Hair Transplant", "Dental")
- `min_rating` (opsiyonel): Minimum puan (0-5)
- `limit` (opsiyonel): Maksimum sonuç (varsayılan: 5)

**Örnek:**
```bash
# Antalya'da diş klinikleri ara
curl "http://localhost:8000/api/clinics/search?city=Antalya&treatment=dental&limit=3"

# Yüksek puanlı klinikler
curl "http://localhost:8000/api/clinics/search?min_rating=4.8&limit=5"

# Genel arama
curl "http://localhost:8000/api/clinics/search?q=saç+ekimi&limit=5"
```

**Yanıt:**
```json
[
  {
    "id": "ant_clinic_001",
    "name": "Antmodern Oral & Dental Health Clinic",
    "city": "Antalya",
    "rating": 4.65,
    "phone": "0 242 324 98 98",
    "address": "Fener Mahallesi...",
    "treatments": ["Composite Bonding", "Zirconium Crowns", ...]
  }
]
```

### 2. Otel Arama (ChromaDB)

**Endpoint:** `GET /api/hotels/search`

**Parametreler:**
- `q` (opsiyonel): Arama metni
- `city` (opsiyonel): Şehir filtresi
- `hotel_type` (opsiyonel): Otel tipi (örn: "Medical Hotel")
- `min_rating` (opsiyonel): Minimum puan
- `max_price` (opsiyonel): Maksimum gecelik fiyat ($)
- `limit` (opsiyonel): Maksimum sonuç

**Örnek:**
```bash
# İstanbul'da medikal oteller
curl "http://localhost:8000/api/hotels/search?city=İstanbul&hotel_type=Medical+Hotel"

# Bütçeye uygun oteller
curl "http://localhost:8000/api/hotels/search?max_price=100&limit=3"
```

**Yanıt:**
```json
[
  {
    "id": "hotel_001",
    "name": "İstanbul Medikal Otel & Spa",
    "city": "İstanbul",
    "rating": 4.7,
    "price_per_night": 120,
    "description": "Medikal turizm hastalarına özel...",
    "features": ["Hastaneye 5 dk mesafe", "Hemşire desteği", ...],
    "amenities": ["WiFi", "Kahvaltı Dahil", ...]
  }
]
```

### 3. Akıllı Chat (Ollama + ChromaDB)

**Endpoint:** `POST /api/chat/smart`

**Request Body:**
```json
{
  "message": "Antalya'da iyi bir diş kliniği önerir misin?",
  "sender": "user"
}
```

**Örnek:**
```bash
curl -X POST http://localhost:8000/api/chat/smart \
  -H "Content-Type: application/json" \
  -d '{"message": "Antalya'\''da saç ekimi için klinik arıyorum"}'
```

**Yanıt:**
```json
{
  "response": "Antalya'da saç ekimi için size 3 harika klinik önerebilirim:\n\n1. **Dr. Ömer Özkan Clinic** - Antalya'nın en yüksek puanlı kliniği (4.98/5). FUE ve DHI yöntemleriyle uzman kadrosu var...",
  "sender": "bot"
}
```

### 4. Rasa Chat (Intent + Entity)

**Endpoint:** `POST /api/chat`

**Request Body:**
```json
{
  "message": "İstanbul'da otel arıyorum",
  "sender": "user"
}
```

Bu endpoint Rasa'ya gönderir, Rasa action'lar ChromaDB'yi kullanarak arama yapar.

---

## 🧪 Manuel Test Örnekleri

### Test 1: Klinik Arama
```bash
curl "http://localhost:8000/api/clinics/search?city=Antalya&limit=3" | jq
```

### Test 2: Otel Arama
```bash
curl "http://localhost:8000/api/hotels/search?city=İstanbul&limit=2" | jq
```

### Test 3: Ollama Chat
```bash
curl -X POST http://localhost:8000/api/chat/smart \
  -H "Content-Type: application/json" \
  -d '{"message": "Merhaba, Antalya'\''da diş tedavisi için klinik önerir misin?"}' | jq
```

### Test 4: ChromaDB Doğrudan Test
```bash
cd api_service
python -c "
from app.services.search_service import search_service
results = search_service.search_clinics(city='Antalya', limit=3)
for clinic in results:
    print(f'{clinic[\"name\"]} - {clinic[\"city\"]} - ⭐{clinic[\"rating\"]}')
"
```

---

## 🔧 Sorun Giderme

### ChromaDB Hatası
```
❌ ChromaDB bağlantı hatası
```
**Çözüm:**
```bash
cd api_service
python scripts/prepare_data.py
```

### Ollama Hatası
```
❌ Ollama servisine bağlanılamadı
```
**Çözüm:**
```bash
# Terminal 1'de
ollama serve

# Terminal 2'de model indir
ollama pull llama3
```

### Rasa Hatası
```
❌ Rasa servisine bağlanılamadı
```
**Çözüm:**
```bash
cd rasa_service
rasa train
rasa run --enable-api --port 5005
```

### Import Hatası (pydantic, fastapi vb.)
```bash
pip install -r requirements.txt
```

---

## 📊 Veri Akışı

```
Kullanıcı Sorusu
      ↓
┌─────────────────────────────────────────────┐
│  Frontend (HTML/JS)                         │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│  FastAPI (/api/chat/smart)                  │
└─────────────────────────────────────────────┘
      ↓
      ├──→ ChromaDB (search_service)
      │         ↓
      │    Klinik/Otel Bulundu
      │         ↓
      └──→ Ollama (ollama_service)
                ↓
           Türkçe Öneri Üretildi
                ↓
           Kullanıcıya Yanıt
```

---

## 🎯 Sonraki Adımlar

1. ✅ **ChromaDB hazır** - Veriler yüklendi
2. ✅ **Ollama entegrasyonu** - LLM çalışıyor
3. ✅ **API endpoint'leri** - Search ve chat hazır
4. ⏳ **Frontend entegrasyonu** - `frontend/index.html` güncellenecek
5. ⏳ **Rasa action'ları** - Rasa'nın actions.py'si API'yi çağıracak

---

## 📝 API Swagger Dökümanı

Tarayıcıda açın:
```
http://localhost:8000/docs
```

Burada tüm endpoint'leri görebilir ve test edebilirsiniz.

---

## 🤝 Destek

Sorun yaşarsanız:
1. `python scripts/test_services.py` çalıştırın
2. Hangi servisin çalışmadığını görün
3. Yukarıdaki "Sorun Giderme" bölümünü uygulayın
