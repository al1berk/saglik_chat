// Chat Logic - Rasa ile entegre
class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.useRealAPI = true; // true = Rasa kullan, false = mock data
    }

    // Mesaj gönder (ana fonksiyon - index.html'deki sendMessage'ı override eder)
    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;
        
        this.addUserMessage(message);
        this.userInput.value = '';
        this.showTyping();

        try {
            if (this.useRealAPI) {
                // Gerçek Rasa API kullan
                const responses = await window.apiService.sendMessage(message);
                this.hideTyping();
                
                if (responses && responses.length > 0) {
                    for (const response of responses) {
                        this.addBotMessage({ text: response.response });
                        await this.delay(500); // Mesajlar arası kısa gecikme
                    }
                } else {
                    // Rasa yanıt vermediyse fallback
                    this.addBotMessage({ 
                        text: 'Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen tekrar deneyin.' 
                    });
                }
            } else {
                // Mock data kullan (test için)
                await this.delay(1500);
                this.hideTyping();
                const response = this.getMockResponse(message);
                this.addBotMessage(response);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();
            
            // Hata mesajı göster
            this.addBotMessage({
                text: `❌ <strong>Bağlantı Hatası</strong><br><br>
                Backend servisi çalışmıyor olabilir. Lütfen şunları kontrol edin:<br><br>
                1. API servisi çalışıyor mu? <code>cd api_service && python main.py</code><br>
                2. Rasa servisi çalışıyor mu? <code>rasa run</code><br>
                3. Rasa actions çalışıyor mu? <code>rasa run actions</code><br><br>
                Teknik detay: ${error.message}`
            });
        }
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

    // Mock response (test için)
    getMockResponse(message) {
        const msg = message.toLowerCase();
        
        if (msg.includes('saç ekimi') || msg.includes('saç')) {
            return {
                text: `💇‍♂️ <strong>SAÇ EKİMİ BİLGİSİ</strong><br><br>
                Saç ekimi, saç köklerinin sağlıklı bölgelerden alınıp dökülme olan bölgelere nakledilmesi işlemidir.<br><br>
                <strong>Yöntemler:</strong><br>
                • FUE: 1.800€ - 2.500€<br>
                • DHI: 2.200€ - 3.000€<br><br>
                <strong>Süre:</strong> 6-8 saat işlem, 2-3 gün konaklama<br><br>
                📞 Randevu için bizimle iletişime geçin!`,
                quickReplies: ['Randevu Al', 'Fiyat Detayları', 'Klinikler']
            };
        }
        
        if (msg.includes('merhaba') || msg.includes('selam')) {
            return {
                text: 'Merhaba! 👋 Size nasıl yardımcı olabilirim?',
                quickReplies: ['Saç Ekimi', 'Diş Tedavisi', 'Estetik', 'Otel']
            };
        }
        
        return {
            text: 'Size nasıl yardımcı olabilirim? Saç ekimi, diş tedavisi, estetik operasyonlar ve konaklama hakkında bilgi verebilirim.',
            quickReplies: ['Tedaviler', 'Fiyatlar', 'Randevu Al']
        };
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
            console.log('Backend health:', health);
            return health.status === 'healthy';
        } catch (error) {
            console.warn('Backend offline, fallback to mock mode');
            this.useRealAPI = false;
            return false;
        }
    }
}

// Global instance oluştur
const chatManager = new ChatManager();

// DOM yüklendiğinde
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🏥 Sağlık Chat başlatılıyor...');
    
    // Sağlık kontrolü yap
    const isHealthy = await chatManager.checkHealth();
    
    if (!isHealthy) {
        console.warn('⚠️ Backend çalışmıyor, mock mode aktif');
    } else {
        console.log('✅ Backend bağlantısı başarılı');
    }
    
    // Input'a focus
    chatManager.userInput.focus();
});

// Global fonksiyonları override et
window.sendMessage = () => chatManager.sendMessage();
window.sendQuickMessage = (text) => chatManager.sendQuickMessage(text);
window.handleKeyPress = (event) => chatManager.handleKeyPress(event);
