// Extension popup script

document.addEventListener('DOMContentLoaded', async () => {
    const statusDiv = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    const loginBtn = document.getElementById('login-btn');
    const clearBtn = document.getElementById('clear-token-btn');

    // Check if logged in
    const storage = await chrome.storage.local.get(['auth_token']);
    const token = storage.auth_token;

    if (token) {
        statusDiv.className = 'status success';
        statusText.textContent = '✅ Logged in and ready';
        loginBtn.textContent = 'Open Dashboard';
    } else {
        statusDiv.className = 'status error';
        statusText.textContent = '❌ Not logged in';
        loginBtn.textContent = 'Login Required';
    }

    // Open login/dashboard page
    loginBtn.addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:3000/' });
    });

    // Clear token
    clearBtn.addEventListener('click', async () => {
        await chrome.storage.local.clear();
        statusDiv.className = 'status error';
        statusText.textContent = '❌ Session cleared';
        loginBtn.textContent = 'Login Required';
    });
});
