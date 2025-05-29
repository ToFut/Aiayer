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
                    
                    // Handle screen frame data
                    if (type === 'screen_frame') {
                        this.handleScreenFrame(payload);
                        window.dispatchEvent(new CustomEvent('screen-frame-received', {
                            detail: payload
                        }));
                    }
                    
                    // Handle automation execution overlays
                    if (type === 'automation_overlay') {
                        this.handleAutomationOverlay(payload);
                        window.dispatchEvent(new CustomEvent('automation-overlay-update', {
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
    
    handleScreenFrame(frameData) {
        // Process incoming screen frame data
        try {
            // Store latest frame data
            this.latestScreenFrame = frameData;
            
            // Create image URL from base64 data
            if (frameData.data && frameData.format === 'compressed_jpeg') {
                const imageUrl = `data:image/jpeg;base64,${frameData.data}`;
                
                // Update screen display
                this.updateScreenDisplay(imageUrl, frameData);
                
                console.log(`Screen frame received: ${frameData.width}x${frameData.height} @ ${frameData.fps.toFixed(1)}fps`);
            }
        } catch (error) {
            console.error('Error handling screen frame:', error);
        }
    }
    
    handleAutomationOverlay(overlayData) {
        // Process automation execution overlay data
        try {
            // Store automation overlay data
            this.currentAutomationOverlay = overlayData;
            
            // Update overlay visualization
            this.updateAutomationOverlay(overlayData);
            
            console.log(`Automation overlay: ${overlayData.action} on ${overlayData.target}`);
        } catch (error) {
            console.error('Error handling automation overlay:', error);
        }
    }
    
    updateScreenDisplay(imageUrl, frameData) {
        // Update screen viewer with new frame
        const screenViewer = document.querySelector('.screen-viewer-image');
        if (screenViewer) {
            screenViewer.src = imageUrl;
            screenViewer.dataset.frameId = frameData.frame_id;
            screenViewer.dataset.timestamp = frameData.timestamp;
        }
        
        // Update cursor position if available
        if (frameData.cursor_position) {
            this.updateCursorPosition(frameData.cursor_position, frameData.width, frameData.height);
        }
        
        // Update UI elements overlay
        if (frameData.ui_elements && frameData.ui_elements.length > 0) {
            this.updateUIElementsOverlay(frameData.ui_elements, frameData.width, frameData.height);
        }
    }
    
    updateCursorPosition(cursorPos, screenWidth, screenHeight) {
        // Update cursor overlay position
        const cursor = document.querySelector('.cursor-overlay');
        if (cursor) {
            const viewerRect = document.querySelector('.screen-viewer').getBoundingClientRect();
            const scaleX = viewerRect.width / screenWidth;
            const scaleY = viewerRect.height / screenHeight;
            
            cursor.style.left = `${cursorPos[0] * scaleX}px`;
            cursor.style.top = `${cursorPos[1] * scaleY}px`;
            cursor.style.display = 'block';
        }
    }
    
    updateUIElementsOverlay(uiElements, screenWidth, screenHeight) {
        // Update UI elements overlay
        const container = document.querySelector('.ui-elements-overlay');
        if (!container) return;
        
        // Clear existing overlays
        container.innerHTML = '';
        
        const viewerRect = document.querySelector('.screen-viewer').getBoundingClientRect();
        const scaleX = viewerRect.width / screenWidth;
        const scaleY = viewerRect.height / screenHeight;
        
        // Add UI element overlays
        uiElements.forEach(element => {
            if (element.bounds && element.bounds.length >= 4) {
                const [x, y, width, height] = element.bounds;
                
                const elementOverlay = document.createElement('div');
                elementOverlay.className = `ui-element-overlay ${element.type}`;
                elementOverlay.style.left = `${x * scaleX}px`;
                elementOverlay.style.top = `${y * scaleY}px`;
                elementOverlay.style.width = `${width * scaleX}px`;
                elementOverlay.style.height = `${height * scaleY}px`;
                elementOverlay.title = element.text || element.type;
                
                container.appendChild(elementOverlay);
            }
        });
    }
    
    updateAutomationOverlay(overlayData) {
        // Update automation execution overlay
        const overlay = document.querySelector('.automation-execution-overlay');
        if (!overlay) return;
        
        // Show execution indicator
        overlay.style.display = 'block';
        overlay.innerHTML = '';
        
        if (overlayData.target_position) {
            const indicator = document.createElement('div');
            indicator.className = `execution-indicator ${overlayData.action}`;
            indicator.style.left = `${overlayData.target_position.x}px`;
            indicator.style.top = `${overlayData.target_position.y}px`;
            indicator.textContent = overlayData.action.toUpperCase();
            
            overlay.appendChild(indicator);
            
            // Auto-hide after animation
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 2000);
        }
    }
    
    // Request screen sharing to start
    requestScreenSharing() {
        this.send('start_screen_sharing', {
            resolution: 'auto',
            fps: 15,
            compression: 85
        });
    }
    
    // Stop screen sharing
    stopScreenSharing() {
        this.send('stop_screen_sharing', {});
    }
}
