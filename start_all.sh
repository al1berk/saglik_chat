#!/bin/bash
# Tüm servisleri başlat - macOS/Linux

echo "🏥 Sağlık Chat Servisleri Başlatılıyor..."
echo "========================================"

# Terminal 1: API Service
echo ""
echo "📡 Terminal 1: API Service başlatılıyor..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/api_service && python main.py"'

sleep 2

# Terminal 2: Rasa Server
echo "🤖 Terminal 2: Rasa Server başlatılıyor..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/rasa_service && rasa run --enable-api --port 5005"'

sleep 2

# Terminal 3: Rasa Actions
echo "⚡ Terminal 3: Rasa Actions başlatılıyor..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/rasa_service && rasa run actions"'

sleep 2

# Terminal 4: Ollama
echo "🧠 Terminal 4: Ollama başlatılıyor..."
osascript -e 'tell app "Terminal" to do script "ollama serve"'

sleep 2

# Terminal 5: Frontend
echo "🌐 Terminal 5: Frontend başlatılıyor..."
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/frontend && python3 -m http.server 8080"'

echo ""
echo "✅ Tüm servisler başlatıldı!"
echo ""
echo "📋 Servis Adresleri:"
echo "   • API:      http://localhost:8000"
echo "   • Rasa:     http://localhost:5005"
echo "   • Actions:  http://localhost:5055"
echo "   • Ollama:   http://localhost:11434"
echo "   • Frontend: http://localhost:8080"
echo ""
echo "🌐 Tarayıcıda aç: http://localhost:8080"
echo ""
