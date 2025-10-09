# 🏥 Sağlık Turizmi AI - Entegre Sistem Kullanım Kılavuzu

## 📋 Genel Bakış

Bu sistem artık **tam entegre** çalışıyor:
- ✅ **Rasa NLU**: Intent ve entity extraction
- ✅ **Ollama LLM**: Açık uçlu sorular için akıllı yanıtlar
- ✅ **MongoDB**: Kullanıcı profilleri ve conversation geçmişi
- ✅ **FastAPI**: Backend API servisi
- ✅ **Frontend**: Gerçek zamanlı chatbot arayüzü

## 🚀 Başlangıç

### 1. Tüm Servisleri Başlatın

#### Terminal 1: MongoDB
```bash
# MongoDB'yi başlatın (eğer kurulu değilse: brew install mongodb-community)
mongod --dbpath /usr/local/var/mongodb
```

#### Terminal 2: Ollama
```bash
# Ollama'yı başlatın
ollama serve

# Llama3 modelini indirin (ilk kullanımda)
ollama pull llama3
```

#### Terminal 3: FastAPI Backend
```bash
cd /Users/aliberkyesilduman/saglik_chat
python api_service/main.py
```

#### Terminal 4: Rasa Actions Server
```bash
cd /Users/aliberkyesilduman/saglik_chat/rasa_service
rasa run actions
```

#### Terminal 5: Rasa Server
```bash
cd /Users/aliberkyesilduman/saglik_chat/rasa_service
rasa run --enable-api --cors "*"
```

### 2. Frontend'i Açın

```bash
# Basit HTTP server ile
cd /Users/aliberkyesilduman/saglik_chat/frontend
python -m http.server 8080

# Tarayıcınızda açın:
# http://localhost:8080/chatbot_integrated.html
```

## 🎯 Sistem Mimarisi

```
┌─────────────┐
│  Frontend   │ (HTML/JS)
│  (Port 8080)│
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌─────────────┐                   ┌──────────────┐
│    Rasa     │◄─────────────────►│   FastAPI    │
│ (Port 5005) │                   │  (Port 8000) │
└──────┬──────┘                   └──────┬───────┘
       │                                 │
       │                                 │
       ▼                                 ▼
┌─────────────┐                   ┌──────────────┐
│Rasa Actions│                   │   MongoDB    │
│ (Port 5055)│                   │ (Port 27017) │
└──────┬──────┘                   └──────────────┘
       │
       ▼
┌─────────────┐
│   Ollama    │
│(Port 11434) │
└─────────────┘
```

## 🔥 Özellikler

### 1. Gerçek Zamanlı Servis Durumu
- Frontend üst barında tüm servislerin durumunu görürsünüz
- Rasa, Ollama, MongoDB ve API'nin anlık durumu

### 2. Intent & Entity Detection (Rasa)
Kullanıcı mesajı:
```
"Antalya'da diş implantı yaptırmak istiyorum"
```

Rasa algılar:
- **Intent**: `tedavi_arama_dental` (confidence: 0.95)
- **Entities**: 
  - `sehir`: "Antalya"
  - `tedavi_adi`: "diş implantı"

### 3. Klinik Arama (API + Mock Data)
```javascript
POST /api/clinics/search
{
  "city": "Antalya",
  "treatment": "dental implant"
}

Response:
{
  "total": 3,
  "results": [
    {
      "name": "Antmodern Clinic",
      "rating": 4.8,
      "treatments": ["Dental Implant", "Teeth Whitening"]
    }
  ]
}
```

### 4. MongoDB'ye Otomatik Kayıt
Her kullanıcı mesajı otomatik kaydedilir:

```javascript
// Conversation log
{
  "user_id": "user_1696789123_abc123",
  "sender": "user",
  "text": "Antalya'da diş implantı",
  "intent": "tedavi_arama_dental",
  "entities": [...],
  "confidence": 0.95,
  "timestamp": "2025-10-09T12:30:00Z"
}

// User profile (otomatik güncellenir)
{
  "user_id": "user_1696789123_abc123",
  "preferences": {
    "treatment": "dental implant",
    "city": "Antalya"
  },
  "created_at": "2025-10-09T12:30:00Z"
}
```

### 5. Ollama Fallback
Rasa anlayamadığı sorular için Ollama devreye girer:

```
User: "Antalya'nın havası nasıl?"
Rasa: confidence < 0.7 → Ollama'ya yönlendir
Ollama: "Antalya Akdeniz iklimi ile yıl boyunca ılıman..."
```

### 6. Conversation History
```bash
# API üzerinden geçmiş görüntüleme
GET /api/conversations/{user_id}?limit=50

# Kullanıcı profilini görüntüleme
GET /api/profile/{user_id}
```

## 💬 Örnek Kullanım Senaryoları

### Senaryo 1: Diş Tedavisi Paketi
```
User: Merhaba, diş implantı yaptırmak istiyorum
Bot: ✨ Mükemmel seçim! Hangi şehirde tedavi olmak istersiniz?

User: Antalya
Bot: 📍 Harika! Antalya'da 7 klinik bulundu:
     🏥 Antmodern Clinic (⭐4.8)
     🏥 Markasya Clinic (⭐4.6)

User: İlk kliniği seç
Bot: 🎁 Sizin için paketler hazırlıyorum...
     [3 paket gösterir: Ekonomik, Standart, Premium]

User: Ekonomik paketi istiyorum
Bot: ✅ Rezervasyonunuz alındı!
     📧 Detaylar e-postanıza gönderildi
```

### Senaryo 2: Genel Soru (Ollama)
```
User: Antalya'da havaalanından şehir merkezine nasıl gidilir?
Rasa: [Confidence düşük - Ollama'ya yönlendir]
Bot: 🤖 Antalya Havalimanı'ndan şehir merkezine...
     [Ollama detaylı yanıt verir]
```

### Senaryo 3: Profil Takibi
```
User: (İlk mesaj) Diş tedavisi istiyorum
MongoDB: User profili oluştur

User: (2. mesaj) Bütçem 5000 euro
MongoDB: Profile ekle → budget: 5000

User: (3. mesaj) Antalya'yı tercih ediyorum
MongoDB: Profile ekle → city: Antalya

# Sonraki oturumda
Bot: Merhaba tekrar! Antalya'da diş tedavisi için...
     [Önceki tercihleri hatırlar]
```

## 🧪 Test Komutları

### 1. MongoDB Kontrolü
```bash
# MongoDB bağlantısını test et
mongosh

# Verileri görüntüle
use health_tourism
db.users.find().pretty()
db.conversations.find().limit(10).pretty()
```

### 2. Rasa Test
```bash
# Intent test
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Antalya'\''da diş implantı"}'

# Webhook test
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender":"test_user","message":"Merhaba"}'
```

### 3. API Test
```bash
# Health check
curl http://localhost:8000/health

# Klinik arama
curl -X POST http://localhost:8000/api/clinics/search \
  -H "Content-Type: application/json" \
  -d '{"city":"Antalya","treatment":"dental"}'

# Conversation geçmişi
curl http://localhost:8000/api/conversations/test_user
```

### 4. Ollama Test
```bash
# Model test
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3",
    "prompt": "Antalya nerede?",
    "stream": false
  }'
```

## 📊 MongoDB Collections

### `users` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user_1696789123_abc123",
  "name": "Ahmet Yılmaz",
  "age": 35,
  "preferences": {
    "treatment": "dental implant",
    "city": "Antalya",
    "budget": 5000
  },
  "created_at": ISODate("2025-10-09T12:30:00Z"),
  "updated_at": ISODate("2025-10-09T14:45:00Z")
}
```

### `conversations` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user_1696789123_abc123",
  "sender": "user",
  "text": "Antalya'da diş implantı",
  "intent": "tedavi_arama_dental",
  "entities": [
    {"entity": "sehir", "value": "Antalya"},
    {"entity": "tedavi_adi", "value": "diş implantı"}
  ],
  "confidence": 0.95,
  "timestamp": ISODate("2025-10-09T12:30:00Z")
}
```

### `bookings` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user_1696789123_abc123",
  "clinic_name": "Antmodern Clinic",
  "treatment": "dental implant",
  "hotel_name": "Delphin Palace",
  "appointment_date": "2025-11-15",
  "costs": {
    "treatment": 2000,
    "hotel": 1400,
    "total": 4150
  },
  "status": "pending",
  "created_at": ISODate("2025-10-09T14:45:00Z")
}
```

## 🔧 Sorun Giderme

### Rasa bağlanamıyor
```bash
# Port kontrolü
lsof -i :5005

# Rasa'yı yeniden başlat
cd rasa_service
rasa run --enable-api --cors "*" --debug
```

### MongoDB bağlanamıyor
```bash
# MongoDB durumunu kontrol et
brew services list | grep mongodb

# MongoDB'yi başlat
brew services start mongodb-community

# Logları kontrol et
tail -f /usr/local/var/log/mongodb/mongo.log
```

### Ollama yanıt vermiyor
```bash
# Ollama servisini kontrol et
ollama list

# Modeli test et
ollama run llama3 "Merhaba"

# Servisi yeniden başlat
killall ollama
ollama serve
```

### Frontend bağlantı hatası
1. Tarayıcı Console'u açın (F12)
2. Network tab'ında istekleri kontrol edin
3. CORS hatası varsa FastAPI CORS ayarlarını kontrol edin

## 📈 Analytics API'leri

### Intent İstatistikleri
```bash
GET /api/analytics/intents?days=30
```

Response:
```json
{
  "period_days": 30,
  "intent_stats": {
    "tedavi_arama_dental": 145,
    "greet": 230,
    "lokasyon_tercihi": 98
  }
}
```

### Aktif Kullanıcılar
```bash
GET /api/analytics/users?days=7
```

Response:
```json
{
  "period_days": 7,
  "active_users": 42,
  "total_conversations": 856
}
```

## 🎨 Frontend Özellikleri

1. **Servis Durumu Monitörü** (Üst bar)
   - Rasa, Ollama, MongoDB, API durumu

2. **Kategori Seçimi** (Sol sidebar)
   - Diş, Estetik, Göz, Obezite, Ortopedi, Kardiyoloji

3. **Gerçek Zamanlı Mesajlaşma**
   - Typing indicator
   - Mesaj zaman damgası
   - Intent metadata (debug için)

4. **Quick Action Buttons**
   - Bot tarafından önerilen hızlı yanıtlar

5. **Conversation Reset**
   - Yeni sohbet başlatma
   - User ID yenileme

6. **History & Profile**
   - Geçmiş görüntüleme
   - Kullanıcı profili görüntüleme

## 🚀 Production Deployment

### Environment Variables
```bash
# .env dosyası oluştur
MONGODB_URI=mongodb://localhost:27017/
RASA_URL=http://localhost:5005
OLLAMA_URL=http://localhost:11434
API_URL=http://localhost:8000
```

### Docker ile Deploy (Opsiyonel)
```bash
docker-compose up -d
```

## 📝 Notlar

- ✅ Her mesaj MongoDB'ye otomatik kaydedilir
- ✅ User profilleri dinamik olarak güncellenir
- ✅ Rasa actions içinde MongoDB logger kullanılır
- ✅ Ollama fallback sistemi aktif
- ✅ CORS tüm servisler için açık (dev)
- ⚠️ Production'da CORS'u sınırlayın
- ⚠️ MongoDB authentication ekleyin
- ⚠️ API rate limiting ekleyin

## 🎓 Hocanıza Göstermek İçin

1. **Status Bar'ı gösterin** - Tüm servisler online
2. **Bir sohbet başlatın** - "Antalya'da diş implantı"
3. **MongoDB'yi gösterin** - `mongosh` ile verileri
4. **Analytics API'yi gösterin** - Intent istatistikleri
5. **Conversation geçmişini gösterin** - API endpoint ile

Başarılar! 🎉
