/**
 * API Client - Handles all API communication with the backend
 */
const API_BASE_URL = 'http://localhost:8001/api';

class APIClient {
    /**
     * Make a request to the API
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        // Set timeout based on endpoint (5 min for ingest, 3 min for others)
        const timeout = endpoint === '/ingest' ? 300000 : 180000;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            signal: controller.signal,
            ...options,
        };

        try {
            console.log(`[API] Making request to: ${url}`);
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            console.log(`[API] Response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
                }
                throw new Error(errorData.detail || errorData.error || 'Request failed');
            }

            const data = await response.json();
            console.log('[API] Response data:', data);
            return data;
        } catch (error) {
            clearTimeout(timeoutId);
            console.error('[API] Error:', error);

            if (error.name === 'AbortError') {
                throw new Error('Request timed out. The operation is taking longer than expected.');
            }

            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                throw new Error('Cannot connect to backend server. Please make sure the backend is running on port 8001.');
            }

            throw error;
        }
    }

    /**
     * Send a chat message
     * @param {string} message - User message
     * @param {string|null} conversationId - Optional conversation ID
     * @returns {Promise<any>} Chat response
     */
    async chat(message, conversationId = null) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                conversation_id: conversationId,
            }),
        });
    }

    /**
     * Ingest documents from folder
     * @param {string} folderPath - Path to folder containing documents
     * @returns {Promise<any>} Ingestion result
     */
    async ingestDocuments(folderPath = 'DB') {
        return this.request('/ingest', {
            method: 'POST',
            body: JSON.stringify({
                folder_path: folderPath,
            }),
        });
    }

    /**
     * Query ingested documents
     * @param {string} query - Question to ask about documents
     * @returns {Promise<any>} Query result
     */
    async queryDocuments(query) {
        return this.request('/query', {
            method: 'POST',
            body: JSON.stringify({
                query,
            }),
        });
    }

    /**
     * Get list of available agents
     * @returns {Promise<any>} List of agents
     */
    async getAgents() {
        return this.request('/agents', {
            method: 'GET',
        });
    }
}

// Export singleton instance
const apiClient = new APIClient();

