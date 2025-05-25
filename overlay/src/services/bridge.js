import { invoke } from '@tauri-apps/api/tauri';

export class Bridge {
    constructor(options = {}) {
        this.ws = null;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.systemContextData = null;
        this.wsUrl = options.url || 'ws://localhost:8767';  // Connect to enhanced backend with real responses
    }

    async connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('Connected to Python backend');
                this.reconnectAttempts = 0;
                
                // Send registration message
                this.send('register', {
                    client_type: 'ui',
                    version: '1.0.0',
                    capabilities: ['overlay_display', 'user_interaction', 'context_tracking'],
                    timestamp: Date.now()
                });
                
                // Dispatch connection event
                window.dispatchEvent(new CustomEvent('bridge-connected'));
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const { type, payload } = data;
                    
                    console.log(`Received message of type: ${type}`);
                    
                    // Store system context data if applicable
                    if (type === 'sensor_data') {
                        this.systemContextData = payload;
                        window.dispatchEvent(new CustomEvent('system-context-updated', { 
                            detail: payload 
                        }));
                    }
                    
                    if (this.messageHandlers.has(type)) {
                        this.messageHandlers.get(type).forEach(handler => handler(payload));
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('Connection closed');
                
                // Dispatch disconnection event
                window.dispatchEvent(new CustomEvent('bridge-disconnected'));
                
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                window.dispatchEvent(new CustomEvent('bridge-error', {
                    detail: { error }
                }));
            };
        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    send(type, payload) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, payload }));
        } else {
            console.error('WebSocket not connected');
        }
    }

    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }

    off(type, handler) {
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }

    async captureScreen() {
        try {
            return await invoke('capture_screen');
        } catch (error) {
            console.error('Error capturing screen:', error);
            return null;
        }
    }

    async toggleInteraction(shouldInteract) {
        try {
            await invoke('toggle_interaction', { shouldInteract });
        } catch (error) {
            console.error('Error toggling interaction:', error);
        }
    }
}
