#!/usr/bin/env python3
"""
API Servislerini Test Et
ChromaDB, Ollama ve API endpoint'lerini test eder
"""
import requests
import sys
from pathlib import Path

# Renkli output için
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_chromadb():
    """ChromaDB bağlantısını test et"""
    print(f"\n{Colors.BLUE}📦 ChromaDB Testi{Colors.END}")
    try:
        import chromadb
        from app.core.config import settings
        
        client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_PATH))
        clinics = client.get_collection(name=settings.CLINICS_COLLECTION)
        hotels = client.get_collection(name=settings.HOTELS_COLLECTION)
        
        print(f"{Colors.GREEN}✅ ChromaDB bağlantısı başarılı{Colors.END}")
        print(f"   Klinik sayısı: {clinics.count()}")
        print(f"   Otel sayısı: {hotels.count()}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ ChromaDB hatası: {e}{Colors.END}")
        print(f"{Colors.YELLOW}💡 Çözüm: python scripts/prepare_data.py{Colors.END}")
        return False

def test_ollama():
    """Ollama servisini test et"""
    print(f"\n{Colors.BLUE}🤖 Ollama Testi{Colors.END}")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": "Merhaba, test",
                "stream": False
            },
            timeout=10,
            proxies={"http": None, "https": None}
        )
        response.raise_for_status()
        print(f"{Colors.GREEN}✅ Ollama servisi çalışıyor{Colors.END}")
        print(f"   Model: llama3")
        return True
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ Ollama servisine bağlanılamadı{Colors.END}")
        print(f"{Colors.YELLOW}💡 Çözüm: ollama serve{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Ollama hatası: {e}{Colors.END}")
        return False

def test_rasa():
    """Rasa servisini test et"""
    print(f"\n{Colors.BLUE}🧠 Rasa Testi{Colors.END}")
    try:
        response = requests.get(
            "http://localhost:5005/",
            timeout=5
        )
        print(f"{Colors.GREEN}✅ Rasa servisi çalışıyor{Colors.END}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ Rasa servisine bağlanılamadı{Colors.END}")
        print(f"{Colors.YELLOW}💡 Çözüm: cd rasa_service && rasa run --enable-api{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Rasa hatası: {e}{Colors.END}")
        return False

def test_api_endpoints():
    """API endpoint'lerini test et"""
    print(f"\n{Colors.BLUE}🌐 API Endpoint Testleri{Colors.END}")
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("Health Check", "GET", f"{base_url}/health"),
        ("Klinik Arama", "GET", f"{base_url}/api/clinics/search?city=Antalya&limit=3"),
        ("Otel Arama", "GET", f"{base_url}/api/hotels/search?city=İstanbul&limit=3"),
    ]
    
    success_count = 0
    for name, method, url in tests:
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ {name}{Colors.END}")
                success_count += 1
            else:
                print(f"{Colors.RED}❌ {name} (Status: {response.status_code}){Colors.END}")
        except requests.exceptions.ConnectionError:
            print(f"{Colors.RED}❌ {name} - API servisi çalışmıyor{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ {name} - {e}{Colors.END}")
    
    return success_count == len(tests)

def main():
    """Ana test fonksiyonu"""
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🏥 Sağlık Chat - Sistem Testi{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = {
        "ChromaDB": test_chromadb(),
        "Ollama": test_ollama(),
        "Rasa": test_rasa(),
        "API": test_api_endpoints()
    }
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 Test Sonuçları{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    for service, status in results.items():
        status_str = f"{Colors.GREEN}✅ Çalışıyor{Colors.END}" if status else f"{Colors.RED}❌ Çalışmıyor{Colors.END}"
        print(f"{service:15} : {status_str}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n{Colors.GREEN}🎉 Tüm testler başarılı! Sistem hazır.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Bazı servisler çalışmıyor. Yukarıdaki çözümleri uygulayın.{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
