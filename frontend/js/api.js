// API Service - Backend ile iletişim
const API_BASE_URL = 'http://localhost:8000/api';
const RASA_URL = 'http://localhost:5005/webhooks/rest/webhook';

class APIService {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.rasaURL = RASA_URL;
    }

    // Chat mesajı gönder (Direkt Rasa'ya - DEADLOCK ÖNLEME)
    async sendMessage(message, sender = 'user') {
        try {
            // Direkt Rasa'ya gönder (API Service bypass)
            const response = await fetch(this.rasaURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sender: sender,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Rasa response formatını standart formata çevir
            const formattedResponse = data.map(item => ({
                response: item.text || '',
                sender: 'bot'
            }));
            
            return formattedResponse;
        } catch (error) {
            console.error('Rasa API Error:', error);
            
            // Fallback: Hata mesajı göster
            return [{
                response: "❌ Bağlantı Hatası\n\nBackend servisleri çalışmıyor olabilir. Lütfen şunları kontrol edin:\n\n1. API Servisi:\ncd api_service && source ../venv/bin/activate && python main.py\n\n2. Rasa Servisi:\ncd rasa_service && source ../venv/bin/activate && rasa run --enable-api\n\n3. Rasa Actions:\ncd rasa_service && source ../venv/bin/activate && rasa run actions\n\n4. Ollama:\nollama serve\n\nTeknik detay: " + error.message,
                sender: 'bot'
            }];
        }
    }

    // Smart Chat mesajı gönder (Ollama + ChromaDB - Rasa olmadan çalışır)
    async sendSmartMessage(message, sender = 'user') {
        try {
            const response = await fetch(`${this.baseURL}/chat/smart`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    sender: sender
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Smart Chat API Error:', error);
            throw error;
        }
    }

    // Klinik ara (ChromaDB)
    async searchClinics(params = {}) {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`${this.baseURL}/clinics/search?${queryParams}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Clinic search error:', error);
            throw error;
        }
    }

    // Otel ara (ChromaDB)
    async searchHotels(params = {}) {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`${this.baseURL}/hotels/search?${queryParams}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Hotel search error:', error);
            throw error;
        }
    }

    // Sağlık kontrolü
    async healthCheck() {
        try {
            const response = await fetch('http://localhost:8000/health');
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'offline' };
        }
    }
}

// Global API instance
window.apiService = new APIService();
