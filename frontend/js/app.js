/**
 * Main Application Logic
 */

// State
let messages = [];
let conversationId = null;
let isLoading = false;
let agents = [];
let documentCount = 0;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const ingestBtn = document.getElementById('ingestBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const agentList = document.getElementById('agentList');
const docCount = document.getElementById('docCount');
const storeStatus = document.getElementById('storeStatus');
const currentTime = document.getElementById('currentTime');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    fetchAgents();
    setupEventListeners();
});

function updateCurrentTime() {
    if (currentTime) {
        const now = new Date();
        currentTime.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    });

    // Ingest documents
    ingestBtn.addEventListener('click', handleIngestDocuments);

    // Clear chat
    clearChatBtn.addEventListener('click', handleClearChat);

    // Agents dropdown toggle
    const agentsDropdown = document.getElementById('agentsDropdown');
    if (agentsDropdown) {
        agentsDropdown.addEventListener('click', () => {
            const agentList = document.getElementById('agentList');
            if (agentList) {
                agentList.classList.toggle('collapsed');
                agentsDropdown.classList.toggle('active');
            }
        });
    }
}

/**
 * Fetch available agents from backend
 */
async function fetchAgents() {
    try {
        const response = await apiClient.getAgents();
        // Handle both array and object with agents property
        agents = Array.isArray(response) ? response : (response.agents || []);
        updateAgentList();
    } catch (error) {
        console.error('[App] Error fetching agents:', error);
        addMessage('System', `Error fetching agents: ${error.message}. Please ensure the backend is running.`, 'System');
    }
}

/**
 * Update agent list in sidebar
 */
function updateAgentList() {
    if (!agentList) return;

    agentList.innerHTML = '';
    // Start collapsed by default
    agentList.classList.add('collapsed');
    
    agents.forEach(agent => {
        const agentItem = document.createElement('div');
        agentItem.className = 'agent-item';
        agentItem.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 0.25rem;">${agent.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-secondary);">${agent.description || ''}</div>
        `;
        agentList.appendChild(agentItem);
    });
}

/**
 * Handle sending a message
 */
async function handleSendMessage(e) {
    e.preventDefault();
    const message = messageInput.value.trim();

    if (!message || isLoading) return;

    // Add user message
    addMessage('You', message, 'user');
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Show loading
    setLoading(true);

    try {
        console.log('[App] Sending chat message:', message);
        const response = await apiClient.chat(message, conversationId);
        console.log('[App] Chat response received:', response);
        
        // Check if response has content
        if (response && response.response) {
            // Add bot response
            addMessage(
                response.agent || 'DocuScout',
                response.response,
                'bot'
            );
        } else if (response && response.error) {
            // Show error from backend
            addMessage(
                'System',
                `Error: ${response.error}`,
                'System'
            );
        } else {
            // Fallback for unexpected response format
            console.warn('[App] Unexpected response format:', response);
            addMessage(
                'DocuScout',
                'I apologize, but I didn\'t receive a proper response. Please try again or check the backend logs.',
                'bot'
            );
        }

        // Update conversation ID if provided
        if (response && response.conversation_id) {
            conversationId = response.conversation_id;
        }

    } catch (error) {
        console.error('[App] Chat error:', error);
        addMessage(
            'System',
            `Error: ${error.message}. Please make sure the backend server is running on port 8001.`,
            'System'
        );
    } finally {
        setLoading(false);
    }
}

/**
 * Handle document ingestion
 */
async function handleIngestDocuments() {
    if (isLoading) return;

    setLoading(true, 'Uploading documents to Google File Search Store... This may take 2-5 minutes.');
    ingestBtn.disabled = true;

    addMessage('FileReader', '📤 Starting document ingestion... This may take a few minutes. Please wait...', 'bot');

    try {
        console.log('[App] Starting ingestion...');
        const response = await apiClient.ingestDocuments('DB');
        console.log('[App] Ingest response:', response);

        if (response.success) {
            addMessage(
                'FileReader',
                `✅ ${response.message || 'Documents ingested successfully!'}`,
                'bot'
            );

            // Update document count
            const match = response.message?.match(/(\d+)\s+documents?/i);
            if (match) {
                documentCount = parseInt(match[1], 10);
                updateDocumentStatus();
            }

            // Update store status
            if (response.message?.includes('store')) {
                if (storeStatus) {
                    storeStatus.textContent = 'Ready';
                    storeStatus.style.color = 'var(--success)';
                }
            }
        } else {
            addMessage(
                'System',
                `❌ Error: ${response.error || 'Failed to ingest documents'}`,
                'System'
            );
        }
    } catch (error) {
        console.error('[App] Ingest error:', error);
        addMessage(
            'System',
            `❌ Error: ${error.message}. ${error.message.includes('timeout') ? 'The ingestion is taking longer than expected. Please try again.' : 'Please make sure the backend server is running on port 8001.'}`,
            'System'
        );
    } finally {
        setLoading(false);
        ingestBtn.disabled = false;
    }
}

/**
 * Handle clearing chat
 */
function handleClearChat() {
    if (confirm('Are you sure you want to clear all messages?')) {
        messages = [];
        chatMessages.innerHTML = '';
        
        // Add welcome message back
        addMessage(
            'DocuScout',
            'Welcome to DocuScout! I\'m your intelligent risk radar for contracts and documents. How can I help you today?',
            'bot'
        );
    }
}

/**
 * Add a message to the chat
 */
function addMessage(sender, text, type = 'bot') {
    const message = {
        id: Date.now(),
        sender,
        text,
        type,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    messages.push(message);
    renderMessage(message);
    scrollToBottom();
}

/**
 * Render a message in the chat
 */
function renderMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type === 'user' ? 'user-message' : 'bot-message'}`;

    const avatar = message.type === 'user' 
        ? 'You'
        : message.sender === 'System'
        ? '⚠️'
        : message.sender.charAt(0);

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${message.sender}</span>
                <span class="message-time">${message.time}</span>
            </div>
            <div class="message-text">${escapeHtml(message.text)}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
}

/**
 * Update document status display
 */
function updateDocumentStatus() {
    if (docCount) {
        docCount.textContent = documentCount;
    }
}

/**
 * Set loading state
 */
function setLoading(loading, message = 'Processing...') {
    isLoading = loading;
    if (loadingOverlay) {
        loadingOverlay.classList.toggle('active', loading);
        const messageEl = document.getElementById('loadingMessage');
        if (messageEl) {
            messageEl.textContent = message;
        }
    }
    if (sendBtn) sendBtn.disabled = loading;
    if (messageInput) messageInput.disabled = loading;
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

