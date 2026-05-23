/**
 * MedPro Chatbot v2 - AI tư vấn sức khỏe + Đặt lịch nhanh
 */

function toggleChatbot() {
    const chatWindow = document.getElementById('chatbot-window');
    chatWindow.classList.toggle('open');
}

document.getElementById('chatbot-toggle').addEventListener('click', toggleChatbot);

function sendChatFromInput() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    if (message) {
        sendChatMessage(message);
        input.value = '';
    }
}

async function sendChatMessage(message) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const suggestionsContainer = document.getElementById('chat-suggestions');

    appendMessage(message, 'user');
    suggestionsContainer.innerHTML = '';

    // Typing indicator
    const typingEl = document.createElement('div');
    typingEl.className = 'chat-message bot';
    typingEl.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messagesContainer.appendChild(typingEl);
    scrollToBottom();

    try {
        const res = await fetch('/api/chatbot/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await res.json();
        typingEl.remove();

        if (data.success && data.data) {
            const response = data.data;

            // Render message with markdown-like formatting
            let msgHtml = formatBotMessage(response.message);

            // Add doctor cards if available
            if (response.bac_si && response.bac_si.length > 0) {
                msgHtml += '<div class="chat-doctors">';
                response.bac_si.forEach(function(bs) {
                    const price = bs.gia_kham ? parseInt(bs.gia_kham).toLocaleString('vi-VN') : '—';
                    msgHtml += '<div class="chat-doctor-card">';
                    msgHtml += '<div class="chat-doc-info">';
                    msgHtml += '<strong>' + (bs.ten_hien_thi || bs.ho_ten || 'Bác sĩ') + '</strong>';
                    msgHtml += '<span>' + (bs.ten_chuyen_khoa || '') + '</span>';
                    msgHtml += '<span class="chat-doc-price">' + price + 'đ</span>';
                    msgHtml += '</div>';
                    msgHtml += '<a href="/lich-kham/dat-lich/' + bs.id + '" class="chat-book-btn"><i class="fas fa-calendar-plus"></i> Đặt lịch</a>';
                    msgHtml += '</div>';
                });
                msgHtml += '</div>';
            }

            appendMessageHTML(msgHtml, 'bot');

            // Suggestions
            if (response.suggestions) {
                suggestionsContainer.innerHTML = response.suggestions.map(function(s) {
                    return '<button class="chat-suggestion-btn" onclick="sendChatMessage(\'' + s.replace(/'/g, "\\'") + '\')">' + s + '</button>';
                }).join('');
            }

            // Redirect action
            if (response.action === 'redirect' && response.url) {
                setTimeout(function() {
                    appendMessage('👉 Đang chuyển trang...', 'bot');
                    setTimeout(function() { window.location.href = response.url; }, 1000);
                }, 2000);
            }
        }
    } catch (err) {
        typingEl.remove();
        appendMessage('❌ Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.', 'bot');
    }
}

function formatBotMessage(text) {
    if (!text) return '';
    // Bold **text**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    return text;
}

function appendMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message ' + sender;
    msgEl.innerHTML = '<div class="chat-bubble">' + formatBotMessage(text) + '</div>';
    messagesContainer.appendChild(msgEl);
    scrollToBottom();
}

function appendMessageHTML(html, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message ' + sender;
    msgEl.innerHTML = '<div class="chat-bubble">' + html + '</div>';
    messagesContainer.appendChild(msgEl);
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById('chatbot-messages');
    container.scrollTop = container.scrollHeight;
}
