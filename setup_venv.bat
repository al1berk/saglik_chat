@echo off
REM Virtual Environment Kurulum Scripti (Windows)
REM Kullanım: setup_venv.bat

echo ==================================
echo 🐍 Virtual Environment Kurulumu
echo ==================================

REM Python versiyonu kontrolü
echo.
echo 📌 Python versiyonu kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadı!
    echo Lütfen Python 3.8+ yükleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% bulundu

REM Virtual environment oluştur
set VENV_DIR=venv

if exist "%VENV_DIR%" (
    echo.
    echo ⚠️  Virtual environment zaten mevcut.
    set /p RECREATE="Yeniden oluşturmak ister misiniz? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo 🗑️  Eski virtual environment siliniyor...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo 📦 Mevcut virtual environment kullanılacak
        goto :activate
    )
)

echo.
echo 📦 Virtual environment oluşturuluyor...
python -m venv "%VENV_DIR%"
echo ✅ Virtual environment oluşturuldu

:activate
REM Virtual environment'ı aktifleştir
echo.
echo 🔄 Virtual environment aktifleştiriliyor...
call "%VENV_DIR%\Scripts\activate.bat"

REM pip güncelle
echo.
echo ⬆️  pip güncelleniyor...
python -m pip install --upgrade pip

REM Gerekli paketleri yükle
echo.
echo 📥 Gerekli paketler yükleniyor...
echo    Bu işlem biraz zaman alabilir...

REM API Service gereksinimleri
if exist "api_service\requirements.txt" (
    echo.
    echo 📋 API Service paketleri yükleniyor...
    pip install -r api_service\requirements.txt
) else (
    echo ⚠️  api_service\requirements.txt bulunamadı
)

REM Ekstra paketler
echo.
echo 📋 Ekstra paketler yükleniyor...
pip install chromadb flask

REM Rasa için (opsiyonel)
echo.
echo 🤖 Rasa yüklensin mi?
echo    (Büyük bir paket, ~500MB, yükleme uzun sürebilir)
set /p INSTALL_RASA="   Rasa yükle? (y/N): "
if /i "%INSTALL_RASA%"=="y" (
    echo 📥 Rasa yükleniyor...
    pip install rasa
    echo ✅ Rasa yüklendi
) else (
    echo ⏭️  Rasa atlandı (daha sonra yükleyebilirsiniz)
)

REM Kurulum özeti
echo.
echo ==================================
echo ✅ Kurulum Tamamlandı!
echo ==================================
echo.
echo 📝 Sonraki adımlar:
echo    1. Virtual environment'ı aktifleştirin:
echo       venv\Scripts\activate
echo.
echo    2. Veritabanını hazırlayın:
echo       cd api_service
echo       python scripts\prepare_data.py
echo.
echo    3. Web görüntüleyiciyi başlatın:
echo       python scripts\web_viewer.py
echo.
echo    4. Tarayıcıda açın:
echo       http://localhost:8080
echo.
echo    5. Çıkmak için:
echo       deactivate
echo.
echo 🎉 Başarılar!
echo.
pause
