// Content script - Injects AI chat interface with JWT authentication

function injectAIButton() {
    // Check if already injected
    if (document.getElementById('ai-assistant-button')) {
        return;
    }

    // Create floating button
    const button = document.createElement('button');
    button.id = 'ai-assistant-button';
    button.textContent = '🤖 AI';
    button.className = 'ai-assistant-btn';
    document.body.appendChild(button);

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'ai-assistant-window';
    chatWindow.className = 'ai-assistant-window';
    chatWindow.style.display = 'none';
    chatWindow.innerHTML = `
        <div class="ai-assistant-header">
            <span>AI Assistant</span>
            <button id="ai-assistant-close" class="ai-close-btn">×</button>
        </div>
        <div id="ai-assistant-output" class="ai-assistant-output">
            <div class="ai-message ai-message-ai">
                👋 Hello! I can automate OpenEMIS tasks. Try: "Login to OpenEMIS as admin"
            </div>
        </div>
        <div class="ai-assistant-input-container">
            <input type="text" id="ai-assistant-input" placeholder="Ask AI to automate..." />
            <button id="ai-assistant-send" class="ai-send-btn">Send</button>
        </div>
    `;
    document.body.appendChild(chatWindow);

    // Setup event listeners
    setupEventListeners(button, chatWindow);
}

function setupEventListeners(button, chatWindow) {
    const input = document.getElementById('ai-assistant-input');
    const sendBtn = document.getElementById('ai-assistant-send');
    const closeBtn = document.getElementById('ai-assistant-close');

    // Toggle chat window
    button.addEventListener('click', () => {
        const isVisible = chatWindow.style.display === 'block';
        chatWindow.style.display = isVisible ? 'none' : 'block';
        if (!isVisible) {
            input.focus();
        }
    });

    // Close window
    closeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
    });

    // Send message
    const sendMessage = async () => {
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        addMessage('user', message);
        addThinkingIndicator();

        try {
            // Send via background script (handles authentication)
            const response = await chrome.runtime.sendMessage({
                type: 'CHAT_REQUEST',
                data: {
                    message: message,
                    context: { url: window.location.href, title: document.title }
                }
            });

            removeThinkingIndicator();

            if (response.success) {
                addMessage('ai', response.data.response);
            } else {
                addMessage('error', response.error || 'Request failed. Please login at localhost:3000');
            }
        } catch (error) {
            removeThinkingIndicator();
            addMessage('error', error.message);
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

function addMessage(type, content) {
    const output = document.getElementById('ai-assistant-output');
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ai-message-${type}`;
    messageDiv.textContent = content;
    output.appendChild(messageDiv);
    output.scrollTop = output.scrollHeight;
}

function addThinkingIndicator() {
    const output = document.getElementById('ai-assistant-output');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = 'ai-thinking';
    thinkingDiv.className = 'ai-message ai-thinking';
    thinkingDiv.innerHTML = `
        <div class="ai-thinking-dots">
            <span></span><span></span><span></span>
        </div>
        <span>AI is thinking...</span>
    `;
    output.appendChild(thinkingDiv);
    output.scrollTop = output.scrollHeight;
}

function removeThinkingIndicator() {
    const thinking = document.getElementById('ai-thinking');
    if (thinking) thinking.remove();
}

// Inject when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectAIButton);
} else {
    injectAIButton();
}
