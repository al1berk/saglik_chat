# 🏥 Sağlık Chat Projesi - Yol Haritası

**Son Güncelleme:** 5 Ekim 2025  
**Durum:** Database Hazırlığı Tamamlandı ✅  
**Sıradaki Adım:** RAG Service + Chat API Geliştirme

---

## 📊 Proje Genel Bakış

### Mimari
```
Kullanıcı → Frontend (HTML/JS) 
         ↓
    API Service (FastAPI)
         ↓
    ├── Rasa Service (NLU/Intent/NER)
    ├── ChromaDB (Vector Search)
    ├── RAG Service (Veri Hazırlama)
    └── Ollama (LLM - Cevap Üretme)
```

### Teknoloji Stack
- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Vector DB:** ChromaDB
- **LLM:** Ollama (Llama3)
- **NLU:** Rasa
- **Frontend:** HTML/CSS/JS (Vanilla)

---

## ✅ TAMAMLANAN ADIMLAR (Phase 1: Database)

### 1. Database Altyapısı ✅
- [x] SQLite veritabanı kurulumu
- [x] 4 tablo oluşturuldu:
  - `clinics` (189 kayıt)
  - `hotels` (60 kayıt)
  - `appointments` (randevu sistemi)
  - `chat_history` (sohbet geçmişi)

### 2. Klinik Verisi ✅
- [x] 189 klinik eklendi
- [x] 41 farklı tedavi tipi
- [x] Her tedaviye fiyat eklendi (price + currency)
- [x] Rating, adres, telefon bilgileri
- [x] 4 şehir: Antalya, İstanbul, Ankara, İzmir

### 3. Otel Verisi ✅
- [x] 60 otel eklendi
- [x] Fiyat, özellikler, konum bilgileri
- [x] API endpoints hazır

### 4. Çok Dilli Veri Hazırlığı ✅
- [x] `treatment_details.json` oluşturuldu
  - 41 tedavi için detaylı bilgi
  - Fiyat aralıkları (min-max)
  - Süre bilgisi (duration_days)
  - Kategori (Dental, Hair Transplant, etc.)
  - **6 dilde açıklama** (tr, en, de, ar, ru, nl)
  
- [x] `translations.json` oluşturuldu
  - 41 tedavi çevirisi (6 dil)
  - 9 UI element çevirisi
  - Tam çok dilli destek

### 5. Randevu Sistemi ✅
- [x] Appointment model ve schema
- [x] CRUD işlemleri
- [x] API endpoints (8 endpoint)
- [x] Durum takibi (pending, confirmed, completed, cancelled)
- [x] Email/SMS tracking
- [x] Migration script

### 6. ChromaDB Kurulumu ✅
- [x] ChromaDB yüklendi
- [x] Vector collections oluşturuldu
- [x] Similarity search hazır

### 7. Ollama Kurulumu ✅
- [x] Ollama yüklendi
- [x] Llama3 modeli indirildi
- [x] Test edildi (Türkçe desteği OK)

---

## 🎯 Yapılacaklar Listesi

### 1. OLLAMA KURULUMU (30 dk)
**Amaç:** Yerel LLM kullanarak Türkçe cevaplar üretmek

#### Adımlar:
```bash
# 1. Ollama'yı indir ve kur
# macOS için: https://ollama.ai/download
brew install ollama

# 2. Ollama'yı başlat
ollama serve

# 3. Türkçe destekli model indir
ollama pull llama2
# veya
ollama pull mistral

# 4. Test et
ollama run llama2 "Merhaba, nasılsın?"
```

#### Entegrasyon:
- `api_service/app/core/ollama.py` dosyası oluştur
- Ollama client wrapper yaz
- System prompt ekle (Türkçe, tıbbi turizm uzmanı)

---

### 2. RASA KURULUMU VE EĞİTİM (1-2 saat)
**Amaç:** Kullanıcı girdilerinden intent ve entity çıkarmak

#### Adımlar:
```bash
# 1. Rasa'yı kur
cd rasa_service
pip install rasa

# 2. Training data hazırla (nlu.yml)
# - search_clinic intenti için 20+ örnek
# - search_hotel intenti için 20+ örnek
# - Entity'ler: city, treatment, price_range

# 3. Config dosyasını ayarla
# - Pipeline: LanguageModelFeaturizer + DIETClassifier
# - Türkçe NLP için

# 4. Modeli train et
rasa train

# 5. Rasa server'ı başlat
rasa run --enable-api --cors "*"
```

#### Training Data Örnekleri:
```yaml
# nlu.yml
- intent: search_clinic
  examples: |
    - Antalya'da diş kliniği arıyorum
    - İstanbul'da plastik cerrahi yapan yerler
    - Ankara'da göz hastanesi öner
    - [Antalya](city)'da [diş tedavisi](treatment) yapan klinikler
    - [İzmir](city)'de iyi bir [göz doktoru](treatment)

- intent: search_hotel
  examples: |
    - Antalya'da otel arıyorum
    - Hastaneye yakın ucuz otel
    - 5 yıldızlı spa oteli
```

---

### 3. API ENDPOİNTLERİ OLUŞTURMA (2-3 saat)
**Amaç:** Frontend ile backend'i bağlamak

#### Yapılacak Dosyalar:

**A. Chat Endpoint** (`app/api/endpoints/chat.py`)
```python
@router.post("/chat")
async def chat(message: str):
    # 1. Rasa'ya gönder → Intent + Entities al
    # 2. ChromaDB'de ara → Klinikleri/Otelleri bul
    # 3. Ollama'ya gönder → Doğal dil cevabı üret
    # 4. Cevabı döndür
```

**B. Search Service** (`app/services/search_service.py`)
```python
class SearchService:
    def search_clinics(city: str, treatment: str, limit: int = 5):
        # ChromaDB'de filtreleme ve arama
        
    def search_hotels(city: str, min_price: float, max_price: float):
        # ChromaDB'de filtreleme ve arama
```

**C. Rasa Service** (`app/services/rasa_service.py`)
```python
class RasaService:
    async def parse(text: str) -> Dict:
        # Rasa API'ye istek at
        # Intent ve entities döndür
```

**D. Ollama Service** (`app/core/ollama.py`)
```python
class OllamaService:
    def generate_response(prompt: str, context: List[Dict]) -> str:
        # Ollama'ya istek at
        # Türkçe cevap üret
```

---

### 4. ENTEGRASYON TESTLERİ (1 saat)
**Test Senaryoları:**

```python
# Test 1: Klinik Arama
Input: "Antalya'da diş kliniği arıyorum"
Expected:
  - Intent: search_clinic
  - Entity: {city: "Antalya", treatment: "diş"}
  - Results: 5+ klinik döner

# Test 2: Otel Arama
Input: "İstanbul'da ucuz otel"
Expected:
  - Intent: search_hotel
  - Entity: {city: "İstanbul", price_range: "low"}
  - Results: Oteller döner

# Test 3: Öneri
Input: "Hangi kliniği önerirsin?"
Expected:
  - Intent: ask_recommendation
  - Ollama cevabı döner
```

---

### 5. FRONTEND OLUŞTURMA (2-3 saat)
**Amaç:** Kullanıcı dostu chat arayüzü

#### Özellikler:
- Chat balonu tasarımı
- Mesaj gönderme/alma
- Klinik kartları gösterme
- Otel kartları gösterme
- Loading animasyonu
- Hata mesajları

#### Teknoloji:
- HTML/CSS/JavaScript (Vanilla)
- Bootstrap 5
- Font Awesome icons
- Fetch API

---

## 📋 Öncelik Sırası

### Hemen Yapılacaklar (Bug gibi)
1. ✅ ChromaDB metadata temizliği (YAPILDI)
2. ✅ Web viewer fiyat → telefon/adres (YAPILDI)

### Kısa Vadeli (Bu hafta)
1. **Ollama kurulumu ve test** ⬅️ ŞİMDİ BU
2. **Rasa NLU training data hazırlama**
3. **Rasa modelini train etme**

### Orta Vadeli (Gelecek hafta)
4. API endpoints oluşturma
5. Servisler arası entegrasyon
6. Test senaryoları

### Uzun Vadeli (2 hafta)
7. Frontend geliştirme
8. UI/UX iyileştirmeleri
9. Production deployment

---

## 🚀 Hızlı Başlangıç Komutları

```bash
# Terminal 1: ChromaDB hazırla
cd api_service
source ../venv/bin/activate
python scripts/prepare_data.py

# Terminal 2: Ollama başlat
ollama serve

# Terminal 3: Rasa train et
cd rasa_service
rasa train
rasa run --enable-api

# Terminal 4: API server başlat
cd api_service
source ../venv/bin/activate
python main.py

# Terminal 5: Frontend serve
cd frontend
python -m http.server 8000
```

---

## 🔍 Sonraki Adım

**ŞİMDİ YAPILACAK:**
1. Ollama'yı kur: `brew install ollama`
2. Modeli indir: `ollama pull llama2`
3. Test et: `ollama run llama2 "Merhaba"`

Hazır olunca devam edelim! 🎯
