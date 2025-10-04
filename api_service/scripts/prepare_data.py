import chromadb
import json
from sentence_transformers import SentenceTransformer

# --- 1. AYARLAR VE BAŞLATMA ---
JSON_FILE = "data.json"      # Okunacak JSON dosyasının adı
CHROMA_PATH = "../medical_clinic_db"    # Veritabanının kaydedileceği klasörün adı
COLLECTION_NAME = "all_clinics"      # Verilerin saklanacağı koleksiyonun (tablonun) adı

# ChromaDB istemcisini başlat. PersistentClient, verileri diske kaydeder.
# Bu sayede programı kapatsan bile veritabanın silinmez.
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Metinleri anlamsal vektörlere çevirecek olan modeli yükle.
# Bu model Türkçe'yi de iyi anlar ve ilk çalıştırmada internetten indirilir.
print("Embedding modeli yükleniyor... (Bu işlem ilk seferde biraz sürebilir)")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Model yüklendi.")

# Koleksiyonu al veya oluştur. Eğer bu isimde bir koleksiyon yoksa oluşturur, varsa onu kullanır.
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"} # Benzerlik hesaplama yöntemi
)

# --- 2. JSON DOSYASINI OKUMA ---
try:
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    clinics = data.get("all_clinics", [])
    print(f"{len(clinics)} adet klinik JSON dosyasından okundu.")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"HATA: '{JSON_FILE}' dosyası okunurken bir sorun oluştu: {e}")
    exit()

# --- 3. VERİLERİ CHROMA FORMATINA DÖNÜŞTÜRME ---
# ChromaDB'ye göndermek için listeleri hazırla
documents_to_add = []
metadatas_to_add = []
ids_to_add = []

print("Veriler ChromaDB'ye eklenecek formata dönüştürülüyor...")
for clinic in clinics:
    # Anlamsal arama için zengin bir 'document' metni oluşturuyoruz.
    # Klinik adı, şehir ve tedavileri birleştirmek, arama kalitesini artırır.
    treatments_text = ", ".join(clinic.get("treatments", []))
    city = clinic.get("city", "Belirtilmemiş")
    document = f"Klinik Adı: {clinic.get('name', 'Bilinmiyor')}. Şehir: {city}. Sunulan Tedaviler: {treatments_text}"
    documents_to_add.append(document)

    # Filtreleme için kullanılacak 'metadata'ları oluşturuyoruz.
    metadatas_to_add.append({
        "name": clinic.get("name") or "Bilinmiyor",
        "rating": float(clinic.get("rating", 0)),
        "address": clinic.get("address") or "",
        "phone": clinic.get("phone") or "",
        "city": city,
        "treatments_str": treatments_text or ""
    })

    # Her klinik için benzersiz 'id' ekliyoruz.
    ids_to_add.append(clinic["id"])

# --- 4. VERİLERİ VERİTABANINA EKLEME ---
# Zaten var olan ID'leri tekrar eklememek için kontrol ediyoruz.
existing_ids = set(collection.get(ids=ids_to_add)['ids'])
new_indices = [i for i, doc_id in enumerate(ids_to_add) if doc_id not in existing_ids]

if new_indices:
    print(f"{len(new_indices)} adet yeni doküman ChromaDB'ye ekleniyor...")
    collection.add(
        documents=[documents_to_add[i] for i in new_indices],
        metadatas=[metadatas_to_add[i] for i in new_indices],
        ids=[ids_to_add[i] for i in new_indices]
    )
    print("Ekleme işlemi başarıyla tamamlandı.")
else:
    print("Yeni doküman bulunamadı. Tüm veriler zaten veritabanında mevcut.")

print(f"Veritabanı hazır! Toplam doküman sayısı: {collection.count()}")