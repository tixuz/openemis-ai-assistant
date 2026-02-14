console.log('content.js loaded and executing.');
// Content script - Injects AI chat interface with JWT authentication

function get_css_selector(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) {
        return null;
    }

    const path = [];
    while (element.nodeType === Node.ELEMENT_NODE) {
        let selector = element.nodeName.toLowerCase();
        if (element.id) {
            selector += '#' + element.id;
            path.unshift(selector);
            break;
        } else {
            let sib = element, nth = 1;
            while ((sib = sib.previousElementSibling)) {
                if (sib.nodeName.toLowerCase() === selector) {
                    nth++;
                }
            }
            if (nth !== 1) {
                selector += ':nth-of-type(' + nth + ')';
            }
        }
        path.unshift(selector);
        element = element.parentNode;
    }
    return path.join(' > ');
}

function is_openemis_page() {
    const footer = document.querySelector('footer');
    const is_openemis = footer && footer.innerText.includes('OpenEMIS');
    console.log('is_openemis_page check: footer content =', footer ? footer.innerText : 'No footer found', '; Is OpenEMIS =', is_openemis);
    return is_openemis;
}

function initializeExtension() {
    console.log('DOMContentLoaded fired.');
    console.log('Is this an OpenEMIS page?', is_openemis_page());

    // Inject AI Button only if it's an OpenEMIS page
    if (is_openemis_page()) {
        injectAIButton();

        // Click listener remains conditional
        document.body.addEventListener('click', (event) => {
            const selector = get_css_selector(event.target);
            console.log(`You've clicked this: ${selector}`);
        });
    }
}

function injectAIButton() {
    console.log('injectAIButton called.');
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

// Добавьте это в content_script.js вашего расширения
let isRecording = false;

function startRecording() {
    isRecording = true;
    console.log("Recording started...");
}

// content_script.js

// 1. Сама функция вычисления селектора
function getSelector(el) {
    if (el.id) return `#${el.id}`; // Самый надежный вариант - ID

    // Если ID нет, строим путь через теги (например, div > span > button)
    let path = [];
    while (el.nodeType === Node.ELEMENT_NODE) {
        let selector = el.nodeName.toLowerCase();
        if (el.className) {
            selector += "." + el.className.trim().replace(/\s+/g, ".");
        }
        path.unshift(selector);
        el = el.parentNode;
    }
    return path.join(" > ");
}

// 2. Слушатель событий, который использует эту функцию
document.addEventListener('click', (e) => {
    if (!isRecording) return;

    const selector = getSelector(e.target); // Вызываем функцию здесь
    console.log("Clicked selector:", selector);

    // Отправляем на ваш FastAPI бэкенд
    sendToBackend({
        type: 'click',
        selector: selector,
        url: window.location.href
    });
});

document.addEventListener('change', (e) => {
    if (!isRecording || e.target.type === 'password') return; // Игнорируем пароли

    const action = {
        type: 'input',
        selector: getSelector(e.target),
        value: e.target.value,
        url: window.location.href,
        timestamp: Date.now()
    };
    sendToBackend(action);
});

function removeThinkingIndicator() {
    const thinking = document.getElementById('ai-thinking');
    if (thinking) thinking.remove();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
    initializeExtension();
}


