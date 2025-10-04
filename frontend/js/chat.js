// Chat Manager - Mesajlaşma mantığını yönetir
class ChatManager {
    constructor() {
        this.api = new ChatAPI();
        this.messagesDiv = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sessionId = this.generateSessionId();
        this.useFallback = true; // API yoksa fallback kullan
        this.init();
    }

    generateSessionId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async init() {
        // API sağlık kontrolü
        const isHealthy = await this.api.healthCheck();
        if (isHealthy) {
            console.log('✅ API bağlantısı başarılı');
            this.useFallback = false;
        } else {
            console.log('⚠️ API bağlantısı yok, fallback modu aktif');
            this.useFallback = true;
        }

        // Event listeners
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        // Kullanıcı mesajını göster
        this.addUserMessage(message);
        this.userInput.value = '';

        // Typing indicator
        this.showTyping();

        try {
            if (this.useFallback) {
                // Fallback: Static responses
                await this.handleFallbackResponse(message);
            } else {
                // Real API: Rasa + ChromaDB + Ollama
                await this.handleAPIResponse(message);
            }
        } catch (error) {
            console.error('Error:', error);
            this.hideTyping();
            this.addBotMessage({
                text: '❌ Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin.',
                quickReplies: ['Ana Menü', 'Yardım']
            });
        }
    }

    async handleAPIResponse(message) {
        try {
            // 1. Rasa'ya gönder (intent detection)
            const rasaResponses = await this.api.sendToRasa(message, this.sessionId);

            this.hideTyping();

            if (rasaResponses && rasaResponses.length > 0) {
                // Rasa'dan gelen yanıtları işle
                for (const response of rasaResponses) {
                    if (response.text) {
                        this.addBotMessage({
                            text: response.text,
                            quickReplies: response.buttons?.map(b => b.title) || []
                        });
                    }

                    // Custom action varsa işle
                    if (response.custom) {
                        await this.handleCustomAction(response.custom);
                    }
                }
            } else {
                // Rasa yanıt vermediyse semantic search yap
                await this.handleSemanticSearch(message);
            }

        } catch (error) {
            console.error('API Response Error:', error);
            // API hatası varsa fallback'e geç
            await this.handleFallbackResponse(message);
        }
    }

    async handleSemanticSearch(message) {
        // Mesajda anahtar kelimelere göre arama yap
        const lowerMsg = message.toLowerCase();

        if (lowerMsg.includes('klinik') || lowerMsg.includes('hastane') || 
            lowerMsg.includes('diş') || lowerMsg.includes('göz') || 
            lowerMsg.includes('saç') || lowerMsg.includes('estetik')) {
            
            // Klinik ara
            const clinics = await this.api.searchClinics(message);
            const formattedResponse = formatClinicResponse(clinics);
            
            this.addBotMessage({
                text: formattedResponse,
                quickReplies: ['Detaylı Bilgi', 'Randevu Al', 'Fiyat Sor']
            });

        } else if (lowerMsg.includes('otel') || lowerMsg.includes('konaklama')) {
            
            // Otel ara
            const hotels = await this.api.searchHotels(message);
            const formattedResponse = formatHotelResponse(hotels);
            
            this.addBotMessage({
                text: formattedResponse,
                quickReplies: ['Rezervasyon', 'Fiyatlar', 'Lokasyon']
            });

        } else {
            // Genel RAG response
            const context = await this.api.searchClinics(message, 3);
            const ragResponse = await this.api.generateResponse(message, context);
            
            this.addBotMessage({
                text: ragResponse.response || ragResponse.text,
                quickReplies: ['Daha Fazla Bilgi', 'Randevu Al']
            });
        }
    }

    async handleCustomAction(customData) {
        // Rasa'dan gelen custom action'ları işle
        if (customData.action === 'search_clinic') {
            const clinics = await this.api.searchClinics(customData.query);
            const formattedResponse = formatClinicResponse(clinics);
            this.addBotMessage({
                text: formattedResponse,
                quickReplies: ['Detaylı Bilgi', 'Randevu Al']
            });
        } else if (customData.action === 'search_hotel') {
            const hotels = await this.api.searchHotels(customData.query);
            const formattedResponse = formatHotelResponse(hotels);
            this.addBotMessage({
                text: formattedResponse,
                quickReplies: ['Rezervasyon', 'Fiyatlar']
            });
        }
    }

    async handleFallbackResponse(message) {
        // Static responses (API olmadan çalışır)
        setTimeout(() => {
            this.hideTyping();
            const response = this.findStaticResponse(message);
            this.addBotMessage(response);
        }, 1500);
    }

    findStaticResponse(message) {
        // Existing static responses from original chatbot.html
        // (responses object'i buraya kopyalanabilir)
        
        const msg = message.toLowerCase();
        
        // Basit pattern matching
        if (msg.includes('merhaba') || msg.includes('selam') || msg.includes('hey')) {
            return {
                text: 'Merhaba! 👋 Size nasıl yardımcı olabilirim?',
                quickReplies: ['Klinikler', 'Tedaviler', 'Fiyatlar', 'Randevu']
            };
        }
        
        if (msg.includes('diş') || msg.includes('implant')) {
            return {
                text: `<h3>🦷 Diş Tedavileri</h3>
                <p>Diş implantı, kaplama ve diğer dental işlemler için size yardımcı olabilirim.</p>
                <div class="info-box">
                    <strong>💰 Ortalama Fiyatlar:</strong><br>
                    • Tek implant: 450€ - 700€<br>
                    • All-on-4: 4.500€ - 7.000€<br>
                    • Kaplama (diş başına): 150€ - 300€
                </div>`,
                quickReplies: ['Klinik Öner', 'Randevu Al', 'Detaylı Bilgi']
            };
        }

        // Default yanıt
        return {
            text: 'Size nasıl yardımcı olabilirim? Tedaviler, klinikler, fiyatlar veya randevu hakkında soru sorabilirsiniz.',
            quickReplies: ['Tedaviler', 'Klinikler', 'Fiyatlar', 'Randevu Al']
        };
    }

    addUserMessage(text) {
        // Welcome screen'i kaldır
        const welcome = this.messagesDiv.querySelector('.welcome-screen');
        if (welcome) welcome.remove();

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">${this.escapeHtml(text)}</div>
        `;

        this.messagesDiv.appendChild(messageDiv);
        this.scrollToBottom();
    }

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

        this.messagesDiv.appendChild(messageDiv);
        this.scrollToBottom();
    }

    sendQuickMessage(text) {
        this.userInput.value = text;
        this.sendMessage();
    }

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
        this.messagesDiv.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    }

    scrollToBottom() {
        this.messagesDiv.scrollTop = this.messagesDiv.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
let chatManager;
document.addEventListener('DOMContentLoaded', () => {
    chatManager = new ChatManager();
    console.log('🤖 Chat Manager initialized');
});

// Global fonksiyonlar (HTML'den erişim için)
function sendMessage() {
    if (chatManager) chatManager.sendMessage();
}

function sendQuickMessage(text) {
    if (chatManager) chatManager.sendQuickMessage(text);
}
