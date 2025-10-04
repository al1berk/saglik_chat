#!/bin/bash
# Virtual Environment Kurulum Scripti
# Kullanım: bash setup_venv.sh

set -e  # Hata durumunda dur

echo "=================================="
echo "🐍 Virtual Environment Kurulumu"
echo "=================================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python versiyonu kontrolü
echo -e "\n${YELLOW}📌 Python versiyonu kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 bulunamadı!${NC}"
    echo "Lütfen Python 3.8+ yükleyin."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION bulundu${NC}"

# Virtual environment oluştur
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo -e "\n${YELLOW}⚠️  Virtual environment zaten mevcut.${NC}"
    read -p "Yeniden oluşturmak ister misiniz? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  Eski virtual environment siliniyor...${NC}"
        rm -rf "$VENV_DIR"
    else
        echo -e "${GREEN}📦 Mevcut virtual environment kullanılacak${NC}"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo -e "\n${YELLOW}📦 Virtual environment oluşturuluyor...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Virtual environment oluşturuldu${NC}"
fi

# Virtual environment'ı aktifleştir
echo -e "\n${YELLOW}🔄 Virtual environment aktifleştiriliyor...${NC}"
source "$VENV_DIR/bin/activate"

# pip güncelle
echo -e "\n${YELLOW}⬆️  pip güncelleniyor...${NC}"
pip install --upgrade pip

# Gerekli paketleri yükle
echo -e "\n${YELLOW}📥 Gerekli paketler yükleniyor...${NC}"
echo -e "${YELLOW}   Bu işlem biraz zaman alabilir...${NC}"

# API Service gereksinimleri
if [ -f "api_service/requirements.txt" ]; then
    echo -e "\n${YELLOW}📋 API Service paketleri yükleniyor...${NC}"
    pip install -r api_service/requirements.txt
else
    echo -e "${YELLOW}⚠️  api_service/requirements.txt bulunamadı${NC}"
fi

# Ekstra paketler (ChromaDB ve Flask için)
echo -e "\n${YELLOW}📋 Ekstra paketler yükleniyor...${NC}"
pip install chromadb flask

# Rasa için (opsiyonel, büyük paket)
echo -e "\n${YELLOW}🤖 Rasa yüklensin mi?${NC}"
echo "   (Büyük bir paket, ~500MB, yükleme uzun sürebilir)"
read -p "   Rasa yükle? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📥 Rasa yükleniyor...${NC}"
    pip install rasa
    echo -e "${GREEN}✅ Rasa yüklendi${NC}"
else
    echo -e "${YELLOW}⏭️  Rasa atlandı (daha sonra yükleyebilirsiniz)${NC}"
fi

# Kurulum özeti
echo -e "\n${GREEN}=================================="
echo "✅ Kurulum Tamamlandı!"
echo "==================================${NC}"
echo -e "\n📝 Sonraki adımlar:"
echo -e "   1. Virtual environment'ı aktifleştirin:"
echo -e "      ${YELLOW}source venv/bin/activate${NC}"
echo -e "\n   2. Veritabanını hazırlayın:"
echo -e "      ${YELLOW}cd api_service${NC}"
echo -e "      ${YELLOW}python scripts/prepare_data.py${NC}"
echo -e "\n   3. Web görüntüleyiciyi başlatın:"
echo -e "      ${YELLOW}python scripts/web_viewer.py${NC}"
echo -e "\n   4. Tarayıcıda açın:"
echo -e "      ${YELLOW}http://localhost:8080${NC}"
echo -e "\n   5. Çıkmak için:"
echo -e "      ${YELLOW}deactivate${NC}"
echo -e "\n${GREEN}🎉 Başarılar!${NC}\n"
