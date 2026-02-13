// API Client - Wrapper for fetch requests

class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    async request(method, path, data = null) {
        const url = `${this.baseURL}/${path}`;

        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.detail || 'Request failed');
            }

            return responseData;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get(path) {
        return this.request('GET', path);
    }

    async post(path, data) {
        return this.request('POST', path, data);
    }

    async put(path, data) {
        return this.request('PUT', path, data);
    }

    async delete(path) {
        return this.request('DELETE', path);
    }
}

// Global API client instance
const apiClient = new APIClient();
