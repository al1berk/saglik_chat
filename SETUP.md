# Sağlık Chat - Kurulum Rehberi

## 📋 Önkoşullar
- Python 3.9+
- macOS / Linux
- 8GB+ RAM
- 10GB disk alanı

---

## 🚀 Adım Adım Kurulum

### 1. Projeyi Klonla
```bash
git clone https://github.com/al1berk/saglik_chat.git
cd saglik_chat
```

### 2. Virtual Environment Oluştur
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. Bağımlılıkları Yükle
```bash
cd api_service
pip install -r requirements.txt
cd ..
```

### 4. ChromaDB Veritabanını Hazırla
```bash
cd api_service
python scripts/prepare_data.py
```

**Çıktı:**
```
✅ clinics.json dosyası okundu: 154 kayıt
✅ Klinikler: Ekleme tamamlandı!
📊 Toplam Klinik: 154
📊 Toplam Otel: 5
```

### 5. Ollama'yı Kur ve Başlat

#### macOS:
```bash
brew install ollama
```

#### Linux:
```bash
curl https://ollama.ai/install.sh | sh
```

#### Modeli İndir:
```bash
ollama pull llama2
# veya Türkçe için daha iyi:
ollama pull mistral
```

#### Test Et:
```bash
ollama run llama2 "Merhaba, nasılsın?"
```

### 6. Rasa'yı Kur ve Train Et
```bash
cd rasa_service
pip install rasa

# Modeli train et
rasa train

# Rasa server'ı başlat
rasa run --enable-api --cors "*" --port 5005
```

### 7. API Server'ı Başlat
```bash
cd api_service
python main.py
```

**Çıktı:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 8. Frontend'i Aç
```bash
cd frontend
python -m http.server 8080
# Tarayıcıda aç: http://localhost:8080
```

---

## 🧪 Test

### ChromaDB Testi:
```bash
cd api_service
python scripts/web_viewer.py
# Tarayıcıda aç: http://localhost:8080
```

### Ollama Testi:
```bash
ollama run llama2 "Antalya'da iyi bir diş kliniği öner"
```

### Rasa Testi:
```bash
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Antalya'da diş kliniği arıyorum"}'
```

### API Testi:
```bash
curl http://localhost:8000/api/clinics?city=Antalya&limit=5
```

---

## 🔧 Çalışan Servisler

| Servis | Port | URL |
|--------|------|-----|
| API Server | 8000 | http://localhost:8000 |
| Rasa Server | 5005 | http://localhost:5005 |
| Ollama | 11434 | http://localhost:11434 |
| Frontend | 8080 | http://localhost:8080 |
| Web Viewer | 8080 | http://localhost:8080 |

---

## ❌ Sorun Giderme

### Hata: "Port already in use"
```bash
# Port'u kullanan process'i bul ve kapat
lsof -ti:8000 | xargs kill -9
```

### Hata: "ChromaDB collection not found"
```bash
# Veritabanını yeniden hazırla
cd api_service
python scripts/prepare_data.py
```

### Hata: "Ollama connection refused"
```bash
# Ollama'yı başlat
ollama serve
```

### Hata: "Rasa model not found"
```bash
# Modeli train et
cd rasa_service
rasa train
```

---

## 📁 Proje Yapısı
```
saglik_chat/
├── api_service/          # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, Ollama
│   │   └── services/    # Rasa, Search
│   ├── data/            # Clinic/Hotel data
│   └── storage/         # ChromaDB
├── rasa_service/         # NLU/Intent
│   ├── data/            # Training data
│   ├── actions/         # Custom actions
│   └── models/          # Trained models
└── frontend/            # HTML/JS UI
```

---

## 🎯 Sonraki Adımlar
1. ✅ ChromaDB hazır
2. ⏳ Ollama kurulumu
3. ⏳ Rasa training
4. ⏳ API endpoints
5. ⏳ Frontend
