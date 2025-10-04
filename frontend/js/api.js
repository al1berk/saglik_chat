// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000/api/v1',
    RASA_URL: 'http://localhost:5005',
    TIMEOUT: 30000
};

// API Helper Functions
class ChatAPI {
    constructor() {
        this.baseUrl = API_CONFIG.BASE_URL;
        this.rasaUrl = API_CONFIG.RASA_URL;
    }

    // Rasa'ya mesaj gönder
    async sendToRasa(message, senderId = 'user') {
        try {
            const response = await fetch(`${this.rasaUrl}/webhooks/rest/webhook`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sender: senderId,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`Rasa API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Rasa API error:', error);
            throw error;
        }
    }

    // ChromaDB'de klinik ara
    async searchClinics(query, limit = 5) {
        try {
            const response = await fetch(`${this.baseUrl}/search/clinics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    limit: limit
                })
            });

            if (!response.ok) {
                throw new Error(`Clinic search error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Clinic search error:', error);
            throw error;
        }
    }

    // Otel ara
    async searchHotels(query, limit = 5) {
        try {
            const response = await fetch(`${this.baseUrl}/search/hotels`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    limit: limit
                })
            });

            if (!response.ok) {
                throw new Error(`Hotel search error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Hotel search error:', error);
            throw error;
        }
    }

    // Ollama ile RAG response üret
    async generateResponse(query, context) {
        try {
            const response = await fetch(`${this.baseUrl}/ollama/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    context: context
                })
            });

            if (!response.ok) {
                throw new Error(`Ollama API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Ollama API error:', error);
            throw error;
        }
    }

    // Sağlık kontrolü
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }
}

// Format helper functions
function formatClinicResponse(clinics) {
    if (!clinics || clinics.length === 0) {
        return '<p>Üzgünüm, aradığınız kriterlere uygun klinik bulunamadı.</p>';
    }

    let html = `<h3>🏥 Bulunan Klinikler (${clinics.length})</h3>`;
    
    clinics.forEach((clinic, index) => {
        html += `
            <div class="treatment-card">
                <h4>${index + 1}. ${clinic.name || 'İsimsiz Klinik'}</h4>
                <div class="info-box">
                    <strong>📍 Konum:</strong> ${clinic.city || 'Belirtilmemiş'}<br>
                    <strong>⭐ Puan:</strong> ${clinic.rating || '-'}/5<br>
                    <strong>📫 Adres:</strong> ${clinic.address || 'Adres bilgisi yok'}<br>
                    <strong>📞 Telefon:</strong> ${clinic.phone || '-'}
                </div>
                ${clinic.treatments && clinic.treatments.length > 0 ? `
                    <p><strong>💊 Tedaviler:</strong></p>
                    ${clinic.treatments.map(t => `<span class="badge badge-primary">${t}</span>`).join('')}
                ` : ''}
            </div>
        `;
    });

    return html;
}

function formatHotelResponse(hotels) {
    if (!hotels || hotels.length === 0) {
        return '<p>Üzgünüm, aradığınız kriterlere uygun otel bulunamadı.</p>';
    }

    let html = `<h3>🏨 Bulunan Oteller (${hotels.length})</h3>`;
    
    hotels.forEach((hotel, index) => {
        html += `
            <div class="treatment-card">
                <h4>${index + 1}. ${hotel.name || 'İsimsiz Otel'}</h4>
                <div class="info-box">
                    <strong>📍 Konum:</strong> ${hotel.city || 'Belirtilmemiş'}<br>
                    <strong>⭐ Puan:</strong> ${hotel.rating || '-'}/5<br>
                    <strong>📫 Adres:</strong> ${hotel.address || 'Adres bilgisi yok'}<br>
                    <strong>📞 Telefon:</strong> ${hotel.phone || '-'}
                </div>
                ${hotel.amenities && hotel.amenities.length > 0 ? `
                    <p><strong>🌟 Özellikler:</strong></p>
                    ${hotel.amenities.map(a => `<span class="badge badge-success">${a}</span>`).join('')}
                ` : ''}
            </div>
        `;
    });

    return html;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatAPI, formatClinicResponse, formatHotelResponse, API_CONFIG };
}
