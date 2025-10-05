// API Service - Backend ile iletişim
const API_BASE_URL = 'http://localhost:8000/api';

class APIService {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    // Chat mesajı gönder (Rasa'ya)
    async sendMessage(message, sender = 'user') {
        try {
            const response = await fetch(`${this.baseURL}/chat/`, {
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
            console.error('API Error:', error);
            throw error;
        }
    }

    // Klinik ara
    async searchClinics(params = {}) {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`${this.baseURL}/search/clinics?${queryParams}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Clinic search error:', error);
            throw error;
        }
    }

    // Otel ara
    async searchHotels(params = {}) {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`${this.baseURL}/search/hotels?${queryParams}`);
            
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
