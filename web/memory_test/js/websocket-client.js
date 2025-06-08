/**
 * WebSocket Client for Memory Testing Interface
 * Handles WebSocket connection to backend memory system
 */

class MemoryWebSocketClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.url = localStorage.getItem('wsUrl') || 'ws://localhost:8769';
        this.apiUrl = localStorage.getItem('apiUrl') || 'http://localhost:8769';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.messageHandlers = {};
        this.connectionListeners = [];
        this.messageQueue = [];
    }

    /**
     * Initialize WebSocket connection
     */
    init() {
        this.logActivity('system', 'Initializing WebSocket connection...');
        this.connect();
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.socket) {
            this.socket.close();
        }

        try {
            this.socket = new WebSocket(this.url);
            
            this.socket.onopen = () => this.handleConnection();
            this.socket.onclose = (event) => this.handleDisconnection(event);
            this.socket.onerror = (error) => this.handleError(error);
            this.socket.onmessage = (event) => this.handleMessage(event);
            
            this.logActivity('system', `Connecting to ${this.url}...`);
        } catch (error) {
            this.logActivity('error', `Connection error: ${error.message}`);
            this.notifyConnectionChange(false);
        }
    }

    /**
     * Handle successful connection
     */
    handleConnection() {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.logActivity('success', 'WebSocket connected');
        this.notifyConnectionChange(true);
        
        // Process any queued messages
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }

    /**
     * Handle disconnection
     */
    handleDisconnection(event) {
        this.isConnected = false;
        this.notifyConnectionChange(false);
        
        // Normal closure, don't attempt to reconnect
        if (event.code === 1000 || event.code === 1001) {
            this.logActivity('system', 'WebSocket disconnected normally');
            return;
        }
        
        this.logActivity('warning', `WebSocket disconnected (code: ${event.code})`);
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            this.logActivity('system', `Reconnecting in ${delay/1000} seconds... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, delay);
        } else {
            this.logActivity('error', 'Maximum reconnection attempts reached');
        }
    }

    /**
     * Handle WebSocket errors
     */
    handleError(error) {
        this.logActivity('error', `WebSocket error: ${error.message || 'Unknown error'}`);
    }

    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.logActivity('system', `Received: ${data.type || 'unknown'} message`);
            
            // Call registered handlers for this message type
            if (data.type && this.messageHandlers[data.type]) {
                this.messageHandlers[data.type].forEach(handler => {
                    try {
                        handler(data);
                    } catch (handlerError) {
                        console.error('Error in message handler:', handlerError);
                    }
                });
            }
        } catch (error) {
            this.logActivity('error', `Failed to parse message: ${error.message}`);
            console.error('WebSocket message error:', error, event.data);
        }
    }

    /**
     * Send a message to the server
     * @param {Object} message - Message to send
     * @returns {boolean} - Whether the message was sent
     */
    sendMessage(message) {
        if (!this.isConnected) {
            this.messageQueue.push(message);
            this.logActivity('warning', 'Message queued: WebSocket not connected');
            return false;
        }
        
        try {
            const messageStr = JSON.stringify(message);
            this.socket.send(messageStr);
            this.logActivity('system', `Sent: ${message.type || 'unknown'} message`);
            return true;
        } catch (error) {
            this.logActivity('error', `Failed to send message: ${error.message}`);
            return false;
        }
    }

    /**
     * Register a handler for a specific message type
     * @param {string} type - Message type
     * @param {Function} handler - Handler function
     */
    onMessage(type, handler) {
        if (!this.messageHandlers[type]) {
            this.messageHandlers[type] = [];
        }
        this.messageHandlers[type].push(handler);
    }

    /**
     * Register a connection state change listener
     * @param {Function} listener - Listener function(isConnected)
     */
    onConnectionChange(listener) {
        this.connectionListeners.push(listener);
    }

    /**
     * Notify all connection listeners of a state change
     * @param {boolean} isConnected - Current connection state
     */
    notifyConnectionChange(isConnected) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(isConnected);
            } catch (error) {
                console.error('Error in connection listener:', error);
            }
        });
    }

    /**
     * Close the WebSocket connection
     */
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Normal closure');
            this.logActivity('system', 'WebSocket disconnected by user');
        }
    }

    /**
     * Update connection settings
     * @param {string} wsUrl - WebSocket URL
     * @param {string} apiUrl - API URL
     */
    updateSettings(wsUrl, apiUrl) {
        this.url = wsUrl;
        this.apiUrl = apiUrl;
        localStorage.setItem('wsUrl', wsUrl);
        localStorage.setItem('apiUrl', apiUrl);
        
        this.logActivity('system', 'Connection settings updated');
        
        // Reconnect if URL changed
        if (this.isConnected) {
            this.disconnect();
        }
        this.connect();
    }

    /**
     * Add a log entry to the activity log
     * @param {string} level - Log level (system, success, warning, error)
     * @param {string} message - Log message
     */
    logActivity(level, message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEvent = new CustomEvent('memory-log', {
            detail: { timestamp, level, message }
        });
        document.dispatchEvent(logEvent);
    }

    /**
     * Make a request to the REST API
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} - Fetch promise
     */
    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            this.logActivity('error', `API request error: ${error.message}`);
            throw error;
        }
    }
}

// Create a singleton instance
const wsClient = new MemoryWebSocketClient();