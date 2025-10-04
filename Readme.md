# Sağlık Chat Asistanı Projesi

## Proje Açıklaması

Sağlık turizmi için geliştirilmiş bir sohbet asistanı projesi. Rasa kullanarak doğal dil işleme (NLU) yapar, FastAPI ile backend servislerini sunar.

## Proje Yapısı

```
saglik_asistani_projesi/
├── rasa_service/              # Rasa Chat Servisi
│   ├── actions/               # Custom actions
│   │   ├── __init__.py
│   │   └── actions.py
│   ├── data/                  # Eğitim verileri
│   │   ├── nlu.yml           # Intent ve entity tanımları
│   │   ├── stories.yml       # Konuşma akışları
│   │   └── rules.yml         # Kısa kurallar
│   ├── models/               # Eğitilmiş modeller
│   ├── tests/                # Test dosyaları
│   ├── config.yml            # Rasa pipeline yapılandırması
│   ├── credentials.yml       # Dış kanal yapılandırmaları
│   ├── domain.yml            # Bot domain tanımları
│   └── endpoints.yml         # Action server adresleri
│
├── api_service/              # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── clinics.py    # Klinik endpointleri
│   │   │   │   └── hotels.py     # Otel endpointleri
│   │   │   └── api.py
│   │   ├── core/
│   │   │   └── config.py         # Proje ayarları
│   │   ├── crud/
│   │   │   ├── crud_clinic.py
│   │   │   └── crud_hotel.py
│   │   ├── db/
│   │   │   └── session.py        # Database bağlantısı
│   │   ├── models/
│   │   │   ├── clinic.py         # Klinik DB modeli
│   │   │   └── hotel.py          # Otel DB modeli
│   │   └── schemas/
│   │       ├── clinic.py         # Klinik şemaları
│   │       └── hotel.py          # Otel şemaları
│   ├── tests/
│   ├── main.py                   # FastAPI uygulaması
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```

## Özellikler

- 🤖 **Rasa NLU**: Türkçe dil desteği ile doğal konuşma
- 🏥 **Klinik Arama**: Şehir ve uzmanlık alanına göre klinik bulma
- 🏨 **Otel Önerileri**: Konaklama seçenekleri
- 🔍 **Akıllı Arama**: Filtreleme ve sıralama özellikleri
- 📊 **RESTful API**: FastAPI ile hızlı ve güvenli API

## Kurulum

### Gereksinimler

- Python 3.8+
- Docker & Docker Compose
- Rasa 3.6.0+

### Adım 1: Projeyi Klonlayın

```bash
git clone <repo-url>
cd saglik_chat
```

### Adım 2: Docker ile Çalıştırın

```bash
docker-compose up --build
```

### Veya Manuel Kurulum

#### Rasa Servisi:

```bash
cd rasa_service
pip install rasa
rasa train
rasa run --enable-api --cors "*"
```

#### Action Server:

```bash
cd rasa_service
rasa run actions
```

#### API Servisi:

```bash
cd api_service
pip install -r requirements.txt
python main.py
```

## Kullanım

### API Endpoints

- **Rasa Chat**: `http://localhost:5005`
- **FastAPI Backend**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### Örnek API İstekleri

#### Klinik Arama:
```bash
curl "http://localhost:8000/api/v1/clinics/search/?city=Istanbul&specialty=Diş"
```

#### Otel Arama:
```bash
curl "http://localhost:8000/api/v1/hotels/search/?city=Ankara&min_rating=4.0"
```

#### Rasa ile Konuşma:
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender":"user","message":"Merhaba"}'
```

## Geliştirme

### Yeni Intent Ekleme

1. `rasa_service/data/nlu.yml` dosyasına yeni örnekler ekleyin
2. `rasa_service/domain.yml` dosyasında intent'i tanımlayın
3. `rasa train` komutuyla modeli yeniden eğitin

### Yeni Endpoint Ekleme

1. `api_service/app/api/endpoints/` altına yeni dosya oluşturun
2. `api_service/app/api/api.py` dosyasında router'ı ekleyin
3. Gerekli model ve schema'ları oluşturun

## Lisans

MIT License

## İletişim

Sorularınız için issue açabilirsiniz.
