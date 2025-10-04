#!/usr/bin/env python3
"""
Web Tabanlı ChromaDB Görüntüleyici
Tarayıcıda klinikleri görüntüle ve ara.

Kullanım:
    python scripts/web_viewer.py
    Tarayıcıda aç: http://localhost:8080
"""

from flask import Flask, render_template_string, request, jsonify
import chromadb
import sys
from pathlib import Path

# Ayarlar
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STORAGE_PATH = PROJECT_ROOT / "storage" / "chroma_db"
CLINICS_COLLECTION = "medical_clinics"
HOTELS_COLLECTION = "medical_hotels"

app = Flask(__name__)

# ChromaDB bağlantısı
chroma_client = None
clinics_collection = None
hotels_collection = None

def init_db():
    """Veritabanı bağlantısını başlat"""
    global chroma_client, clinics_collection, hotels_collection
    try:
        chroma_client = chromadb.PersistentClient(path=str(STORAGE_PATH))
        clinics_collection = chroma_client.get_collection(name=CLINICS_COLLECTION)
        hotels_collection = chroma_client.get_collection(name=HOTELS_COLLECTION)
        print(f"✅ Veritabanına başarıyla bağlanıldı: {STORAGE_PATH}")
        print(f"📊 Toplam klinik: {clinics_collection.count()}")
        print(f"📊 Toplam otel: {hotels_collection.count()}")
        return True
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        print("💡 Önce veritabanını hazırlayın:")
        print("   python scripts/prepare_data.py")
        return False

# HTML Template - Yeni Modern Tasarım
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏥 Sağlık Klinikleri Veritabanı</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
        }
        body {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            padding: 20px 0 50px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main-header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }
        .main-header h1 {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .stats-row {
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card h2 {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-card p {
            margin: 0;
            opacity: 0.9;
        }
        .control-panel {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .nav-tabs {
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 20px;
        }
        .nav-tabs .nav-link {
            border: none;
            color: #666;
            font-weight: 600;
            padding: 12px 25px;
            transition: all 0.3s;
        }
        .nav-tabs .nav-link:hover {
            color: var(--primary);
        }
        .nav-tabs .nav-link.active {
            color: var(--primary);
            border-bottom: 3px solid var(--primary);
            background: none;
        }
        .item-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
            transition: all 0.3s;
            border-left: 5px solid var(--primary);
        }
        .item-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 25px rgba(0,0,0,0.15);
        }
        .item-title {
            color: var(--primary);
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .rating-badge {
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            color: #333;
            padding: 8px 15px;
            border-radius: 25px;
            font-weight: bold;
            display: inline-block;
            box-shadow: 0 2px 10px rgba(255, 215, 0, 0.3);
        }
        .info-row {
            margin: 10px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #555;
        }
        .info-row i {
            width: 20px;
            text-align: center;
        }
        .badge-pill {
            background: var(--primary);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin: 3px;
            display: inline-block;
        }
        .pagination-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }
        .page-link {
            color: var(--primary);
            border: 1px solid #dee2e6;
            margin: 0 2px;
            border-radius: 8px;
        }
        .page-link:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        .page-item.active .page-link {
            background: var(--primary);
            border-color: var(--primary);
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }
        .empty-state i {
            font-size: 4rem;
            color: #ddd;
            margin-bottom: 20px;
        }
        .search-input {
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            padding: 12px 20px;
            font-size: 1.05rem;
        }
        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 10px;
            padding: 12px 30px;
            font-weight: 600;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        .loading-spinner {
            text-align: center;
            padding: 60px;
        }
        .spinner-border {
            width: 4rem;
            height: 4rem;
            border-width: 0.4rem;
        }
    </style>
</head>
<body>
    <div class="container" style="max-width: 1400px;">
        <!-- Header -->
        <div class="main-header">
            <h1><i class="fas fa-hospital-alt"></i> Sağlık Klinikleri Veritabanı</h1>
            <p class="text-muted mb-0">ChromaDB - RAG Sistemi</p>
        </div>

        <!-- Stats -->
        <div class="row stats-row g-4">
            <div class="col-md-4">
                <div class="stat-card">
                    <h2>{{ total_clinics }}</h2>
                    <p><i class="fas fa-hospital"></i> Toplam Klinik</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <h2 id="avgRating">4.85</h2>
                    <p><i class="fas fa-star"></i> Ortalama Rating</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <h2>{{ total_hotels }}</h2>
                    <p><i class="fas fa-hotel"></i> Toplam Otel</p>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="control-panel">
            <!-- Tabs -->
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#clinics-tab" 
                            onclick="switchTab('clinics')">
                        <i class="fas fa-hospital"></i> Klinikler
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#hotels-tab" 
                            onclick="switchTab('hotels')">
                        <i class="fas fa-hotel"></i> Oteller
                    </button>
                </li>
            </ul>

            <!-- Search -->
            <div class="row g-3 mt-2">
                <div class="col-md-9">
                    <input type="text" id="searchInput" class="form-control search-input" 
                           placeholder="🔍 Klinik ara... (örn: diş tedavisi, İstanbul, göz ameliyatı)">
                </div>
                <div class="col-md-3">
                    <button onclick="performSearch()" class="btn btn-primary w-100">
                        <i class="fas fa-search"></i> Ara
                    </button>
                </div>
            </div>
            
            <div class="mt-3">
                <button onclick="showAll()" class="btn btn-outline-secondary me-2">
                    <i class="fas fa-list"></i> Tümünü Göster
                </button>
            </div>
        </div>

        <!-- Results -->
        <div id="results"></div>
        
        <!-- Pagination -->
        <div id="pagination" class="pagination-container" style="display: none;"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentTab = 'clinics';
        let currentPage = 1;
        let perPage = 10;
        let totalItems = 0;

        window.onload = function() {
            loadData();
        };

        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') performSearch();
        });

        function switchTab(tab) {
            currentTab = tab;
            currentPage = 1;
            document.getElementById('searchInput').value = '';
            loadData();
        }

        function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                showAll();
                return;
            }
            
            showLoading();
            const endpoint = currentTab === 'clinics' ? '/api/search' : '/api/search/hotels';
            
            fetch(`${endpoint}?q=${encodeURIComponent(query)}&limit=50`)
                .then(r => r.json())
                .then(data => {
                    const items = currentTab === 'clinics' ? data.clinics : data.hotels;
                    displayItems(items, true);
                })
                .catch(err => showError('Arama sırasında hata oluştu'));
        }

        function showAll() {
            document.getElementById('searchInput').value = '';
            currentPage = 1;
            loadData();
        }

        function loadData(page = 1) {
            currentPage = page;
            showLoading();
            
            const endpoint = currentTab === 'clinics' ? '/api/clinics' : '/api/hotels';
            fetch(`${endpoint}?page=${currentPage}&per_page=${perPage}`)
                .then(r => r.json())
                .then(data => {
                    const items = currentTab === 'clinics' ? data.clinics : data.hotels;
                    totalItems = data.total;
                    displayItems(items);
                    renderPagination(data.total_pages);
                })
                .catch(err => showError('Veri yüklenirken hata oluştu'));
        }

        function displayItems(items, isSearch = false) {
            const resultsDiv = document.getElementById('results');
            
            if (!items || items.length === 0) {
                resultsDiv.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <h3>Sonuç Bulunamadı</h3>
                        <p class="text-muted">Arama kriterlerinize uygun sonuç bulunamadı.</p>
                    </div>
                `;
                document.getElementById('pagination').style.display = 'none';
                return;
            }

            let html = '';
            items.forEach(item => {
                if (currentTab === 'clinics') {
                    html += renderClinicCard(item);
                } else {
                    html += renderHotelCard(item);
                }
            });
            
            resultsDiv.innerHTML = html;
            
            if (!isSearch) {
                document.getElementById('pagination').style.display = 'block';
            } else {
                document.getElementById('pagination').style.display = 'none';
            }
        }

        function renderClinicCard(clinic) {
            const treatments = (clinic.treatments || '').split(',').filter(t => t.trim());
            return `
                <div class="item-card">
                    <div class="row">
                        <div class="col-md-9">
                            <div class="item-title">
                                <i class="fas fa-hospital-alt"></i>
                                <span>${clinic.name}</span>
                            </div>
                            <div class="info-row">
                                <i class="fas fa-map-marker-alt text-danger"></i>
                                <strong>${clinic.city}, ${clinic.country || 'Turkey'}</strong>
                            </div>
                            <div class="info-row">
                                <i class="fas fa-dollar-sign text-success"></i>
                                <span>${clinic.price_range || 'Fiyat bilgisi yok'}</span>
                            </div>
                            <div class="mt-3">
                                ${treatments.slice(0, 8).map(t => 
                                    `<span class="badge-pill">${t.trim()}</span>`
                                ).join('')}
                            </div>
                        </div>
                        <div class="col-md-3 text-end">
                            <div class="rating-badge">
                                ⭐ ${clinic.rating}/5
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderHotelCard(hotel) {
            return `
                <div class="item-card" style="border-left-color: #28a745;">
                    <div class="row">
                        <div class="col-md-9">
                            <div class="item-title" style="color: #28a745;">
                                <i class="fas fa-hotel"></i>
                                <span>${hotel.name}</span>
                            </div>
                            <div class="info-row">
                                <i class="fas fa-map-marker-alt text-danger"></i>
                                <strong>${hotel.city}, ${hotel.country || 'Turkey'}</strong>
                            </div>
                            <div class="info-row">
                                <i class="fas fa-building text-info"></i>
                                <span>${hotel.hotel_type || 'Medical Hotel'}</span>
                            </div>
                            <div class="info-row">
                                <i class="fas fa-dollar-sign text-success"></i>
                                <strong>$${hotel.price_per_night || 0} / gece</strong>
                            </div>
                        </div>
                        <div class="col-md-3 text-end">
                            <div class="rating-badge">
                                ⭐ ${hotel.rating}/5
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderPagination(totalPages) {
            if (totalPages <= 1) {
                document.getElementById('pagination').style.display = 'none';
                return;
            }

            let html = '<nav><ul class="pagination justify-content-center mb-0">';
            
            // Previous
            html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="loadData(${currentPage - 1}); return false;">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>`;

            // Pages
            let start = Math.max(1, currentPage - 2);
            let end = Math.min(totalPages, currentPage + 2);

            if (start > 1) {
                html += `<li class="page-item"><a class="page-link" href="#" onclick="loadData(1); return false;">1</a></li>`;
                if (start > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }

            for (let i = start; i <= end; i++) {
                html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="loadData(${i}); return false;">${i}</a>
                </li>`;
            }

            if (end < totalPages) {
                if (end < totalPages - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
                html += `<li class="page-item"><a class="page-link" href="#" onclick="loadData(${totalPages}); return false;">${totalPages}</a></li>`;
            }

            // Next
            html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="loadData(${currentPage + 1}); return false;">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>`;

            html += '</ul></nav>';
            html += `<div class="text-center mt-3 text-muted">
                Sayfa ${currentPage} / ${totalPages} (Toplam ${totalItems} kayıt)
            </div>`;
            
            document.getElementById('pagination').innerHTML = html;
            document.getElementById('pagination').style.display = 'block';
        }

        function showLoading() {
            document.getElementById('results').innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="text-white mt-3">Yükleniyor...</p>
                </div>
            `;
        }

        function showError(msg) {
            document.getElementById('results').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                    <h3>Hata</h3>
                    <p class="text-muted">${msg}</p>
                </div>
            `;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Ana sayfa"""
    if clinics_collection is None or hotels_collection is None:
        return "❌ Veritabanı bağlantısı yok. Lütfen prepare_data.py'yi çalıştırın.", 500
    
    total_clinics = clinics_collection.count()
    total_hotels = hotels_collection.count()
    return render_template_string(HTML_TEMPLATE, total=total_clinics + total_hotels, total_clinics=total_clinics, total_hotels=total_hotels)


@app.route('/api/clinics')
def get_clinics():
    """Tüm klinikleri veya sayfalama ile getir"""
    if clinics_collection is None:
        return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Tüm verileri al
    result = clinics_collection.get()
    
    # Sayfalama
    start = (page - 1) * per_page
    end = start + per_page
    
    clinics = []
    for i in range(start, min(end, len(result['metadatas']))):
        metadata = result['metadatas'][i]
        clinics.append({
            'id': result['ids'][i],
            'name': metadata.get('name', 'İsimsiz'),
            'city': metadata.get('city', 'Belirtilmemiş'),
            'rating': metadata.get('rating', 0),
            'address': metadata.get('address', '-'),
            'phone': metadata.get('phone', '-'),
            'treatments': metadata.get('treatments', [])
        })
    
    return jsonify({
        'clinics': clinics,
        'total': len(result['metadatas']),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(result['metadatas']) + per_page - 1) // per_page
    })


@app.route('/api/search')
def search_clinics():
    """Klinik ara"""
    if clinics_collection is None:
        return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
    
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Arama sorgusu gerekli'}), 400
    
    # Arama yap
    results = clinics_collection.query(query_texts=[query], n_results=limit)
    
    clinics = []
    if results['metadatas'] and results['metadatas'][0]:
        for i, metadata in enumerate(results['metadatas'][0]):
            clinics.append({
                'id': results['ids'][0][i],
                'name': metadata.get('name', 'İsimsiz'),
                'city': metadata.get('city', 'Belirtilmemiş'),
                'rating': metadata.get('rating', 0),
                'address': metadata.get('address', '-'),
                'phone': metadata.get('phone', '-'),
                'treatments': metadata.get('treatments', [])
            })
    
    return jsonify({
        'clinics': clinics,
        'query': query,
        'count': len(clinics)
    })


@app.route('/api/stats')
def get_stats():
    """İstatistikler"""
    if clinics_collection is None:
        return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
    
    result = clinics_collection.get()
    
    # Şehirlere göre grupla
    cities = {}
    ratings = []
    
    for metadata in result['metadatas']:
        city = metadata.get('city', 'Belirtilmemiş')
        cities[city] = cities.get(city, 0) + 1
        ratings.append(metadata.get('rating', 0))
    
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    return jsonify({
        'total': len(result['metadatas']),
        'cities': cities,
        'avg_rating': round(avg_rating, 2),
        'top_cities': sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]
    })


@app.route('/api/hotels')
def get_hotels():
    """Tüm otelleri veya sayfalama ile getir"""
    if hotels_collection is None:
        return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Tüm verileri al
    result = hotels_collection.get()
    
    # Sayfalama
    start = (page - 1) * per_page
    end = start + per_page
    
    hotels = []
    for i in range(start, min(end, len(result['metadatas']))):
        metadata = result['metadatas'][i]
        hotels.append({
            'id': result['ids'][i],
            'name': metadata.get('name', 'İsimsiz'),
            'city': metadata.get('city', 'Belirtilmemiş'),
            'rating': metadata.get('rating', 0),
            'price_per_night': metadata.get('price_per_night', 0),
            'hotel_type': metadata.get('hotel_type', 'Hotel')
        })
    
    return jsonify({
        'hotels': hotels,
        'total': len(result['metadatas']),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(result['metadatas']) + per_page - 1) // per_page
    })


@app.route('/api/search/hotels')
def search_hotels():
    """Otel ara"""
    if hotels_collection is None:
        return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
    
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Arama sorgusu gerekli'}), 400
    
    # Arama yap
    results = hotels_collection.query(query_texts=[query], n_results=limit)
    
    hotels = []
    if results['metadatas'] and results['metadatas'][0]:
        for i, metadata in enumerate(results['metadatas'][0]):
            hotels.append({
                'id': results['ids'][0][i],
                'name': metadata.get('name', 'İsimsiz'),
                'city': metadata.get('city', 'Belirtilmemiş'),
                'rating': metadata.get('rating', 0),
                'price_per_night': metadata.get('price_per_night', 0),
                'hotel_type': metadata.get('hotel_type', 'Hotel')
            })
    
    return jsonify({
        'hotels': hotels,
        'query': query,
        'count': len(hotels)
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 ChromaDB Web Görüntüleyici")
    print("="*70)
    
    if not init_db():
        print("\n❌ Veritabanı başlatılamadı. Çıkılıyor...")
        sys.exit(1)
    
    print(f"🔗 URL: http://localhost:8080")
    print("⌨️  Durdurmak için: Ctrl+C")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
