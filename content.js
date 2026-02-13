// Function to inject styles
function injectStyles(css) {
    const styleElement = document.createElement('style');
    styleElement.textContent = css;
    document.head.append(styleElement);
}

// Function to inject the AI button
function injectAIButton() {
    const aiButton = document.createElement('button');
    aiButton.id = 'gemini-ai-button';
    aiButton.textContent = 'AI';
    document.body.append(aiButton);

    const chatWindow = document.createElement('div');
    chatWindow.id = 'gemini-chat-window';
    chatWindow.style.display = 'none'; // Hidden by default
    document.body.append(chatWindow);

    const chatInput = document.createElement('input');
    chatInput.type = 'text';
    chatInput.placeholder = 'Ask AI...';
    chatInput.id = 'gemini-chat-input';
    chatWindow.append(chatInput);

    const chatOutput = document.createElement('div');
    chatOutput.id = 'gemini-chat-output';
    chatWindow.append(chatOutput);

    aiButton.addEventListener('click', () => {
        chatWindow.style.display = chatWindow.style.display === 'none' ? 'block' : 'none';
    });

    chatInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const message = chatInput.value;
            chatInput.value = '';
            chatOutput.textContent = `You: ${message}`; // Display user message
            
            try {
                const response = await fetch('http://localhost:8000/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                });
                const data = await response.json();
                chatOutput.textContent += `
AI: ${data.response}`; // Display AI response
            } catch (error) {
                console.error('Error:', error);
                chatOutput.textContent += `
AI: Error connecting to server.`;
            }
        }
    });
}

// Inject styles from styles.css
fetch(chrome.runtime.getURL('styles.css'))
    .then(response => response.text())
    .then(injectStyles)
    .then(injectAIButton)
    .catch(err => console.error('Error loading styles.css:', err));
