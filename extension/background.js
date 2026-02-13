// Background service worker for authentication and messaging

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'CHAT_REQUEST') {
    handleChatRequest(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
});

// Handle chat request with authentication
async function handleChatRequest(data) {
  // Get stored token
  const storage = await chrome.storage.local.get(['auth_token']);
  const token = storage.auth_token;

  if (!token) {
    throw new Error('Not logged in. Please visit http://localhost:3000/login');
  }

  // Make API request to Flask frontend (which proxies to FastAPI)
  const response = await fetch('http://localhost:3000/api/user/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      message: data.message,
      context: data.context || {}
    })
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid
      await chrome.storage.local.remove(['auth_token']);
      throw new Error('Session expired. Please login again.');
    }
    throw new Error(`Request failed: ${response.statusText}`);
  }

  return await response.json();
}
