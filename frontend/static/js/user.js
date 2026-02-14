// User chat interface with thinking indicator and scrollable responses

class ChatInterface {
    constructor() {
        this.chatOutput = document.getElementById('chat-output');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');

        this.setupEventListeners();
        this.loadHistory();
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async loadHistory() {
        try {
            // Load recent chat history
            const response = await apiClient.get('user/history', { limit: 50 });

            if (response.history && response.history.length > 0) {
                // Clear welcome message
                this.chatOutput.innerHTML = '';

                // Add history messages (already sorted newest first from API)
                // Reverse to show oldest first
                const messages = response.history.reverse();

                messages.forEach(msg => {
                    // Add user message
                    this.addMessage('user', msg.message, { fromHistory: true });

                    // Add AI response
                    const options = {
                        scrollable: msg.response.length > 200,
                        fromHistory: true
                    };

                    if (msg.execution_result) {
                        options.executionResult = msg.execution_result;
                    }

                    this.addMessage('ai', msg.response, options);
                });

                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            // Keep welcome message on error
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();

        if (!message) return;

        // Disable input while processing
        this.chatInput.disabled = true;
        this.sendBtn.disabled = true;

        // Add user message
        this.addMessage('user', message);
        this.chatInput.value = '';

        // Show thinking indicator
        const thinkingDiv = this.addThinkingIndicator();

        try {
            // Call chat API
            const response = await apiClient.post('user/chat', {
                message: message,
                context: {}
            });

            // Remove thinking indicator
            thinkingDiv.remove();

            // Add AI response with scrollable content
            this.addMessage('ai', response.response, {
                scrollable: response.response.length > 200,
                executionResult: response.execution_result
            });

        } catch (error) {
            // Remove thinking indicator
            thinkingDiv.remove();

            // Show error
            this.addMessage('error', `❌ Error: ${error.message}`);
        } finally {
            // Re-enable input
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
            this.chatInput.focus();
        }
    }

    addThinkingIndicator() {
        const div = document.createElement('div');
        div.className = 'message thinking';
        div.innerHTML = `
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span class="thinking-text">AI is thinking...</span>
        `;
        this.chatOutput.appendChild(div);
        this.scrollToBottom();
        return div;
    }

    addMessage(type, content, options = {}) {
        const div = document.createElement('div');
        div.className = `message ${type}`;

        if (type === 'user') {
            div.innerHTML = `<strong>You:</strong><br>${this.escapeHtml(content)}`;
        } else if (type === 'ai') {
            if (options.scrollable) {
                div.innerHTML = `
                    <strong>AI Assistant:</strong><br>
                    <div class="message-content scrollable">${this.formatContent(content)}</div>
                `;
            } else {
                div.innerHTML = `<strong>AI Assistant:</strong><br>${this.formatContent(content)}`;
            }

            // Add execution result if available
            if (options.executionResult) {
                const result = options.executionResult;

                // Display screenshot images if available
                if (result.screenshot_data && result.screenshot_data.length > 0) {
                    const screenshotsDiv = document.createElement('div');
                    screenshotsDiv.style.marginTop = '15px';
                    screenshotsDiv.innerHTML = '<strong style="font-size: 14px;">📸 Screenshots:</strong>';

                    result.screenshot_data.forEach((screenshot, index) => {
                        const imgContainer = document.createElement('div');
                        imgContainer.style.marginTop = '10px';
                        imgContainer.style.border = '2px solid #ddd';
                        imgContainer.style.borderRadius = '8px';
                        imgContainer.style.overflow = 'hidden';
                        imgContainer.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

                        const img = document.createElement('img');
                        img.src = `data:image/png;base64,${screenshot.data}`;
                        img.alt = screenshot.filename;
                        img.style.width = '100%';
                        img.style.display = 'block';
                        img.style.cursor = 'pointer';
                        img.title = 'Click to view full size';

                        // Click to open in new tab
                        img.onclick = () => {
                            const newWindow = window.open();
                            newWindow.document.write(`<img src="${img.src}" style="max-width:100%;">`);
                        };

                        const caption = document.createElement('div');
                        caption.style.padding = '8px';
                        caption.style.background = '#f5f5f5';
                        caption.style.fontSize = '12px';
                        caption.style.color = '#666';
                        caption.textContent = screenshot.filename;

                        imgContainer.appendChild(img);
                        imgContainer.appendChild(caption);
                        screenshotsDiv.appendChild(imgContainer);
                    });

                    div.appendChild(screenshotsDiv);
                }
            }
        } else if (type === 'error') {
            div.textContent = content;
        }

        this.chatOutput.appendChild(div);
        this.scrollToBottom();
        return div;
    }

    formatContent(content) {
        // Convert newlines to <br> and preserve formatting
        return this.escapeHtml(content).replace(/\n/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatOutput.scrollTop = this.chatOutput.scrollHeight;
    }
}

// Initialize chat interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});
