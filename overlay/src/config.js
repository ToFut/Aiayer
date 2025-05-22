/**
 * System Configuration
 * 
 * This file contains the configuration settings for the overlay application
 * to connect to the correct backend services.
 */

export const CONFIG = {
    // WebSocket connections
    websockets: {
        // LLM service with context awareness (main chat interface)
        llm: {
            url: 'ws://localhost:8765', // Updated to use WebSocket server port 8765 where LLM service registers
            reconnectAttempts: 10,
            reconnectDelay: 1000,
            debug: false
        },
        
        // Bridge server for sensor data and context integration
        bridge: {
            url: 'ws://localhost:8765', // Updated to use the same WebSocket server as LLM service
            reconnectAttempts: 10,
            reconnectDelay: 1000,
            debug: false
        },
        
        // Backend server for additional services
        backend: {
            url: 'ws://localhost:8767',
            reconnectAttempts: 10,
            reconnectDelay: 1000,
            debug: false
        }
    },
    
    // Feature flags
    features: {
        // Enable context-aware responses
        contextAwareness: true,
        
        // Enable conversation memory
        conversationMemory: true,
        
        // Enable sensor data integration
        sensorIntegration: true
    },
    
    // UI settings
    ui: {
        // Auto-reconnect behavior
        autoReconnect: true,
        
        // Show debug information
        showDebugInfo: false,
        
        // Context display settings
        showContextData: true
    }
};

export default CONFIG;