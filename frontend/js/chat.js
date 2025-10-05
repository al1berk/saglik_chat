// Chat Logic - Rasa ile entegre
class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.useRasa = true; // RASA ÖNCELİKLİ - Ollama'ya sadece Rasa actions üzerinden bağlanır
    }

    // Mesaj gönder (ana fonksiyon)
    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;
        
        this.addUserMessage(message);
        this.userInput.value = '';
        this.showTyping();

        try {
            // ÖNCELİKLE RASA KULLAN
            // Akış: Frontend → Rasa (NLU) → Rasa Actions (ChromaDB + Ollama) → Yanıt
            const responses = await window.apiService.sendMessage(message);
            this.hideTyping();
            
            if (responses && responses.length > 0) {
                for (const response of responses) {
                    this.addBotMessage({ text: response.response });
                    await this.delay(500);
                }
            } else {
                // Rasa yanıt vermediyse
                this.addBotMessage({ 
                    text: 'Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen tekrar deneyin.' 
                });
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();
            
            // Hata mesajı göster
            this.addBotMessage({
                text: `❌ <strong>Bağlantı Hatası</strong><br><br>
                Backend servisleri çalışmıyor olabilir. Lütfen şunları kontrol edin:<br><br>
                <strong>1. API Servisi:</strong><br>
                <code>cd api_service && source ../venv/bin/activate && python main.py</code><br><br>
                <strong>2. Rasa Servisi:</strong><br>
                <code>cd rasa_service && source ../venv/bin/activate && rasa run --enable-api</code><br><br>
                <strong>3. Rasa Actions:</strong><br>
                <code>cd rasa_service && source ../venv/bin/activate && rasa run actions</code><br><br>
                <strong>4. Ollama:</strong><br>
                <code>ollama serve</code><br><br>
                <small>Teknik detay: ${error.message}</small>`,
                quickReplies: ['Yardım', 'Test Et']
            });
        }
    }

    // İlgili sonuçları göster (klinik/otel) - Smart Chat için
    async showRelatedResults(message) {
        const msg = message.toLowerCase();
        
        try {
            // Klinik araması
            if (msg.includes('klinik') || msg.includes('hastane') || msg.includes('doktor') || 
                msg.includes('diş') || msg.includes('saç') || msg.includes('estetik')) {
                
                const clinics = await window.apiService.searchClinics({ 
                    q: message, 
                    limit: 3 
                });
                
                if (clinics && clinics.length > 0) {
                    await this.delay(500);
                    this.addClinicResults(clinics);
                }
            }
            
            // Otel araması
            if (msg.includes('otel') || msg.includes('konaklama') || msg.includes('kalacak')) {
                const hotels = await window.apiService.searchHotels({ 
                    q: message, 
                    limit: 3 
                });
                
                if (hotels && hotels.length > 0) {
                    await this.delay(500);
                    this.addHotelResults(hotels);
                }
            }
        } catch (error) {
            console.error('Related results error:', error);
        }
    }

    // Klinik sonuçlarını göster
    addClinicResults(clinics) {
        let html = '<div class="treatment-card"><h3>🏥 Bulunan Klinikler</h3>';
        
        clinics.forEach((clinic, index) => {
            html += `
                <div class="info-box">
                    <strong>${index + 1}. ${clinic.name}</strong><br>
                    📍 ${clinic.city}<br>
                    ⭐ Puan: ${clinic.rating}/5<br>
                    📞 ${clinic.phone || 'Belirtilmemiş'}<br>
            `;
            
            if (clinic.treatments && clinic.treatments.length > 0) {
                html += `<br><span class="badge badge-primary">${clinic.treatments.slice(0, 3).join('</span> <span class="badge badge-primary">')}</span>`;
            }
            
            html += '</div>';
        });
        
        html += '</div>';
        
        this.addBotMessage({ 
            text: html,
            quickReplies: ['Daha Fazla Klinik', 'Randevu Al', 'Fiyat Bilgisi']
        });
    }

    // Otel sonuçlarını göster
    addHotelResults(hotels) {
        let html = '<div class="treatment-card"><h3>🏨 Bulunan Oteller</h3>';
        
        hotels.forEach((hotel, index) => {
            html += `
                <div class="info-box">
                    <strong>${index + 1}. ${hotel.name}</strong><br>
                    📍 ${hotel.city}<br>
                    ⭐ Puan: ${hotel.rating}/5<br>
                    💰 Gecelik: $${hotel.price_per_night}<br>
            `;
            
            if (hotel.features && hotel.features.length > 0) {
                html += `<br><span class="badge badge-success">${hotel.features.slice(0, 3).join('</span> <span class="badge badge-success">')}</span>`;
            }
            
            html += '</div>';
        });
        
        html += '</div>';
        
        this.addBotMessage({ 
            text: html,
            quickReplies: ['Daha Fazla Otel', 'Rezervasyon Yap', 'Yakındaki Klinikler']
        });
    }

    // Kullanıcı mesajı ekle
    addUserMessage(text) {
        // Welcome screen'i kaldır
        const welcome = this.messagesContainer.querySelector('.welcome-screen');
        if (welcome) welcome.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">${this.escapeHtml(text)}</div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // Bot mesajı ekle
    addBotMessage(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        let quickRepliesHTML = '';
        if (response.quickReplies && response.quickReplies.length > 0) {
            quickRepliesHTML = `
                <div class="quick-replies">
                    ${response.quickReplies.map(reply => 
                        `<button class="quick-reply-btn" onclick="chatManager.sendQuickMessage('${reply}')">${reply}</button>`
                    ).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">🏥</div>
            <div class="message-content">
                ${response.text}
                ${quickRepliesHTML}
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // Quick message gönder
    sendQuickMessage(text) {
        this.userInput.value = text;
        this.sendMessage();
    }

    // Typing indicator göster
    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">🏥</div>
            <div class="typing-indicator active">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    // Typing indicator gizle
    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    }

    // Scroll to bottom
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    // Delay helper
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // HTML escape
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Enter tuşu kontrolü
    handleKeyPress(event) {
        if (event.key === 'Enter') {
            this.sendMessage();
        }
    }

    // Sağlık kontrolü
    async checkHealth() {
        try {
            const health = await window.apiService.healthCheck();
            console.log('✅ Backend health:', health);
            
            if (health.status === 'healthy') {
                console.log('🤖 Rasa modu aktif');
                console.log('📊 Akış: Kullanıcı → Rasa (NLU/Intent/NER) → Actions (ChromaDB + Ollama) → Yanıt');
                return true;
            }
            return false;
        } catch (error) {
            console.error('❌ Backend offline:', error.message);
            return false;
        }
    }
}

// Global instance oluştur
const chatManager = new ChatManager();

// DOM yüklendiğinde
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🏥 Sağlık Chat başlatılıyor...');
    console.log('🤖 MOD: Rasa + ChromaDB + Ollama (Tam Entegrasyon)');
    
    // Sağlık kontrolü yap
    const isHealthy = await chatManager.checkHealth();
    
    if (!isHealthy) {
        console.warn('⚠️ Backend çalışmıyor. Lütfen servisleri başlatın.');
        
        // Kullanıcıya bilgi ver
        chatManager.addBotMessage({
            text: `⚠️ <strong>Backend Bağlantısı Yok</strong><br><br>
            Lütfen aşağıdaki servisleri sırayla başlatın:<br><br>
            <strong>Terminal 1 - API:</strong><br>
            <code>cd api_service && source ../venv/bin/activate && python main.py</code><br><br>
            <strong>Terminal 2 - Rasa:</strong><br>
            <code>cd rasa_service && source ../venv/bin/activate && rasa run --enable-api</code><br><br>
            <strong>Terminal 3 - Rasa Actions:</strong><br>
            <code>cd rasa_service && source ../venv/bin/activate && rasa run actions</code><br><br>
            <strong>Terminal 4 - Ollama:</strong><br>
            <code>ollama serve</code><br><br>
            Ardından sayfayı yenileyin (F5).`,
            quickReplies: ['Yardım', 'Dokümantasyon']
        });
    } else {
        console.log('✅ Backend bağlantısı başarılı!');
        console.log('🎯 AKIŞ:');
        console.log('   1. Kullanıcı mesajı → Rasa (NLU)');
        console.log('   2. Rasa → Intent + Entities');
        console.log('   3. Rasa Actions → ChromaDB arama');
        console.log('   4. Rasa Actions → Ollama öneri');
        console.log('   5. Yanıt → Kullanıcı');
    }
    
    // Input'a focus
    chatManager.userInput.focus();
});

// Global fonksiyonları override et
window.sendMessage = () => chatManager.sendMessage();
window.sendQuickMessage = (text) => chatManager.sendQuickMessage(text);
window.handleKeyPress = (event) => chatManager.handleKeyPress(event);
