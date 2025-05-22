import { invoke } from '@tauri-apps/api/tauri';

/**
 * Enhanced WebSocket Bridge
 * Robust connection handling between Tauri app and backend services
 * with support for memory integration and context awareness
 */
export class EnhancedBridge {
    /**
     * Create a new enhanced bridge
     * @param {Object} options - Configuration options
     * @param {string} options.url - WebSocket URL (default: ws://localhost:8767)
     * @param {number} options.reconnectAttempts - Max reconnect attempts (default: 10)
     * @param {number} options.reconnectDelay - Initial delay between reconnects in ms (default: 1000)
     * @param {boolean} options.debug - Enable debug logging (default: false)
     */
    constructor(options = {}) {
        // Configuration
        this.url = options.url || 'ws://localhost:8767';  // Backend server port
        this.maxReconnectAttempts = options.reconnectAttempts || 10;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.debug = options.debug || false;
        
        // State
        this.ws = null;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.autoReconnect = true;
        this.isConnecting = false;
        this.lastPingTime = 0;
        this.pingInterval = null;
        this.connectionStatus = 'disconnected';
        
        // Context and memory
        this.systemContextData = null;
        this.conversationHistory = [];
        this.memoryEnabled = true;
        
        // Bind methods to preserve 'this' context
        this._handleOpen = this._handleOpen.bind(this);
        this._handleMessage = this._handleMessage.bind(this);
        this._handleClose = this._handleClose.bind(this);
        this._handleError = this._handleError.bind(this);
    }
    
    /**
     * Log debug messages if debug mode is enabled
     * @private
     */
    _log(...args) {
        if (this.debug) {
            console.log('[EnhancedBridge]', ...args);
        }
    }
    
    /**
     * Connect to the WebSocket server
     * @returns {Promise} Resolves when connected, rejects on failure
     */
    async connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            this._log('WebSocket already connected or connecting');
            return Promise.resolve();
        }
        
        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        this.isConnecting = true;
        this.connectionStatus = 'connecting';
        this._dispatchStatusChange();
        
        return new Promise((resolve, reject) => {
            try {
                this._log(`Connecting to ${this.url}`);
                
                // Close existing connection if any
                if (this.ws) {
                    try {
                        this.ws.close();
                    } catch (e) {
                        this._log('Error closing existing WebSocket:', e);
                    }
                    this.ws = null;
                }
                
                this.ws = new WebSocket(this.url);
                
                // Set a connection timeout
                const connectionTimeout = setTimeout(() => {
                    if (this.isConnecting) {
                        this._log('Connection timeout');
                        this.ws.close();
                        reject(new Error('Connection timeout'));
                    }
                }, 5000);
                
                // Connection opened
                this.ws.onopen = (event) => {
                    clearTimeout(connectionTimeout);
                    this._handleOpen(event, resolve);
                };
                
                // Listen for messages
                this.ws.onmessage = this._handleMessage;
                
                // Connection closed
                this.ws.onclose = (event) => {
                    clearTimeout(connectionTimeout);
                    this._handleClose(event, reject);
                };
                
                // Connection error
                this.ws.onerror = (event) => {
                    clearTimeout(connectionTimeout);
                    this._handleError(event, reject);
                };
                
            } catch (error) {
                this.isConnecting = false;
                this.connectionStatus = 'error';
                this._dispatchStatusChange();
                this._log('Error creating WebSocket:', error);
                reject(error);
                this._scheduleReconnect();
            }
        });
    }
    
    /**
     * Handle WebSocket open event
     * @private
     */
    _handleOpen(event, resolve) {
        this.isConnecting = false;
        this.connectionStatus = 'connected';
        this.reconnectAttempts = 0;
        this._log('WebSocket connected');
        
        // Start ping interval to keep connection alive
        this._startPingInterval();
        
        // Send registration message
        this.send('register', {
            client_type: 'ui',
            version: '2.0.0',
            capabilities: ['memory', 'context', 'notification'],
            timestamp: Date.now()
        });
        
        // Request initial context
        this.send('context_request', {
            requestId: this._generateId(),
            timestamp: Date.now()
        });
        
        // Dispatch connection event
        this._dispatchStatusChange();
        window.dispatchEvent(new CustomEvent('bridge-connected'));
        
        // Resolve promise
        if (resolve) resolve();
    }
    
    /**
     * Handle WebSocket message event
     * @private
     */
    _handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Handle ping/pong messages
            if (data.type === 'ping') {
                this.send('pong', { timestamp: Date.now() });
                return;
            }
            if (data.type === 'pong') {
                this.lastPingTime = Date.now();
                return;
            }
            if (data.type === 'registration_confirmed') {
                this._log('Registration confirmed by server');
                return;
            }
            if (data.type === 'error') {
                this._log('Server error:', data.message);
                return;
            }
            
            // Handle other messages
            if (this.messageHandlers.has(data.type)) {
                this.messageHandlers.get(data.type).forEach(handler => {
                    try {
                        handler(data);
                    } catch (error) {
                        this._log('Error in message handler:', error);
                    }
                });
            }
            
            // Store context data
            if (data.type === 'sensor_data') {
                this.systemContextData = data;
                window.dispatchEvent(new CustomEvent('system-context-updated', { 
                    detail: data 
                }));
            }
            
            // Store query responses in conversation history
            if (data.type === 'query_response' && this.memoryEnabled) {
                this.conversationHistory.push({
                    role: 'assistant',
                    content: data.response,
                    timestamp: Date.now()
                });
            }
            
        } catch (error) {
            this._log('Error handling message:', error);
        }
    }
    
    /**
     * Handle WebSocket close event
     * @private
     */
    _handleClose(event, reject) {
        this.isConnecting = false;
        this._stopPingInterval();
        
        const wasConnected = this.connectionStatus === 'connected';
        this.connectionStatus = 'disconnected';
        this._log(`WebSocket closed: ${event.code} ${event.reason}`);
        
        // Dispatch disconnection event
        this._dispatchStatusChange();
        window.dispatchEvent(new CustomEvent('bridge-disconnected'));
        
        // Schedule reconnect if not closed intentionally
        if (this.autoReconnect && event.code !== 1000) {
            this._scheduleReconnect();
        }
        
        // Reject promise if connection was being established
        if (reject && !wasConnected) {
            reject(new Error(`Connection closed: ${event.code} ${event.reason}`));
        }
    }
    
    /**
     * Handle WebSocket error event
     * @private
     */
    _handleError(event, reject) {
        this.isConnecting = false;
        this.connectionStatus = 'error';
        this._log('WebSocket error:', event);
        
        // Stop ping interval
        this._stopPingInterval();
        
        // Close existing connection if any
        if (this.ws) {
            try {
                this.ws.close();
            } catch (e) {
                this._log('Error closing WebSocket:', e);
            }
            this.ws = null;
        }
        
        // Dispatch error event
        window.dispatchEvent(new CustomEvent('bridge-error', { 
            detail: { 
                error: event.error || 'WebSocket error',
                timestamp: Date.now()
            }
        }));
        
        // Reject promise if this was a connection attempt
        if (reject) {
            reject(new Error('WebSocket error'));
        }
        
        // Schedule reconnect if auto-reconnect is enabled
        if (this.autoReconnect) {
            this._scheduleReconnect();
        }
    }
    
    /**
     * Schedule a reconnection attempt
     * @private
     */
    _scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this._log('Max reconnect attempts reached');
            this.connectionStatus = 'failed';
            this._dispatchStatusChange();
            window.dispatchEvent(new CustomEvent('bridge-failed', { 
                detail: { 
                    attempts: this.reconnectAttempts,
                    timestamp: Date.now()
                }
            }));
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
        
        this._log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        this.connectionStatus = 'reconnecting';
        this._dispatchStatusChange();
        
        window.dispatchEvent(new CustomEvent('bridge-reconnecting', { 
            detail: { 
                attempt: this.reconnectAttempts,
                delay: delay,
                timestamp: Date.now()
            }
        }));
        
        this.reconnectTimer = setTimeout(() => {
            this.connect().catch(error => {
                this._log('Reconnect failed:', error);
            });
        }, delay);
    }
    
    /**
     * Start the ping interval to keep connection alive
     * @private
     */
    _startPingInterval() {
        this._stopPingInterval();
        this.lastPingTime = Date.now();
        
        this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                // Send ping message every 25 seconds (slightly before server's ping)
                this.send('ping', { timestamp: Date.now() });
                
                // Check if we've received a pong
                const elapsed = Date.now() - this.lastPingTime;
                if (elapsed > 90000) { // No response for 90 seconds
                    this._log('No pong received, reconnecting...');
                    this.disconnect();
                    this.connect().catch(error => {
                        this._log('Reconnect after ping timeout failed:', error);
                    });
                }
            }
        }, 25000);
    }
    
    /**
     * Stop the ping interval
     * @private
     */
    _stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    /**
     * Dispatch connection status change event
     * @private
     */
    _dispatchStatusChange() {
        window.dispatchEvent(new CustomEvent('bridge-status-changed', {
            detail: { status: this.connectionStatus }
        }));
    }
    
    /**
     * Generate a unique ID
     * @private
     * @returns {string} A UUID v4 compatible ID
     */
    _generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    /**
     * Send a message to the server
     * @param {string} type - Message type
     * @param {object} payload - Message payload
     * @returns {boolean} - True if message was sent successfully
     */
    send(type, payload) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this._log('Cannot send message, WebSocket not connected');
            return false;
        }
        
        try {
            const message = JSON.stringify({ type, payload });
            this.ws.send(message);
            
            // Store user messages in conversation history
            if (type === 'user_interaction' && payload.type === 'query' && this.memoryEnabled) {
                this.conversationHistory.push({
                    role: 'user',
                    content: payload.query,
                    timestamp: Date.now()
                });
            }
            
            return true;
        } catch (error) {
            console.error('Error sending message:', error);
            return false;
        }
    }
    
    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        this.autoReconnect = false; // Prevent automatic reconnection
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        this._stopPingInterval();
        
        if (this.ws) {
            try {
                this.ws.close(1000, 'Client disconnecting');
            } catch (error) {
                this._log('Error closing WebSocket:', error);
            }
            this.ws = null;
        }
        
        this.connectionStatus = 'disconnected';
        this._dispatchStatusChange();
    }
    
    /**
     * Register a message handler
     * @param {string} type - Message type to handle
     * @param {function} handler - Callback function to handle the message
     */
    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }
    
    /**
     * Remove a message handler
     * @param {string} type - Message type
     * @param {function} handler - Handler to remove
     */
    off(type, handler) {
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    /**
     * Enable/disable automatic reconnection
     * @param {boolean} enable - Whether to enable auto reconnection
     */
    setAutoReconnect(enable) {
        this.autoReconnect = !!enable;
    }
    
    /**
     * Enable/disable conversation memory
     * @param {boolean} enable - Whether to enable memory
     */
    setMemoryEnabled(enable) {
        this.memoryEnabled = !!enable;
    }
    
    /**
     * Get the current conversation history
     * @returns {Array} - Conversation history
     */
    getConversationHistory() {
        return [...this.conversationHistory];
    }
    
    /**
     * Clear the conversation history
     */
    clearConversationHistory() {
        this.conversationHistory = [];
    }
    
    /**
     * Get the current connection status
     * @returns {string} - Connection status
     */
    getStatus() {
        return this.connectionStatus;
    }
    
    /**
     * Get the current system context data
     * @returns {object|null} - Context data
     */
    getContextData() {
        return this.systemContextData;
    }
    
    /**
     * Capture screen via Tauri API
     * @returns {Promise<string>} - Screen capture data
     */
    async captureScreen() {
        try {
            return await invoke('capture_screen');
        } catch (error) {
            console.error('Error capturing screen:', error);
            return null;
        }
    }
    
    /**
     * Toggle interaction mode via Tauri API
     * @param {boolean} shouldInteract - Whether interaction should be enabled
     * @returns {Promise<void>}
     */
    async toggleInteraction(shouldInteract) {
        try {
            await invoke('toggle_interaction', { shouldInteract });
        } catch (error) {
            console.error('Error toggling interaction:', error);
            throw error;
        }
    }
}