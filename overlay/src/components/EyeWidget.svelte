<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    import { Bridge } from '../services/bridge';
    import ScreenViewer from './ScreenViewer.svelte';
    
    // Create event dispatcher
    const dispatch = createEventDispatcher();
    
    // Props
    export let onToggleInteraction = () => {};
    
    // State
    let bridge;
    let isExpanded = false;
    let isMinimized = true;
    let isInteractive = false;
    let connectionStatus = 'disconnected';
    let isConnecting = false;
    let messages = [];
    let userInput = '';
    let isThinking = false;
    let notificationCount = 0;
    let sensorData = null;
    let persistToMemory = true;
    let showScreenViewer = false;
    
    // Position tracking for draggable widget
    let widgetX = 20;
    let widgetY = 20;
    let dragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    
    // Mouse tracking
    let mouseX = 0;
    let mouseY = 0;
    let eyeRotation = 0;
    let eyeScale = 1;
    let glowIntensity = 0;
    let widgetElement;
    
    onMount(() => {
        setupBridge();
        
        // Set initial position from localStorage if available
        try {
            const savedPosition = localStorage.getItem('eyeWidgetPosition');
            if (savedPosition) {
                const { x, y } = JSON.parse(savedPosition);
                widgetX = x;
                widgetY = y;
            }
        } catch (e) {
            console.error('Could not load saved position:', e);
        }
        
        // Add global event listeners
        window.addEventListener('mouseup', handleGlobalMouseUp);
        window.addEventListener('mousemove', handleGlobalMouseMove);
        
        // Setup keyboard shortcuts
        window.addEventListener('keydown', handleKeydown);
        
        // Add mouse move listener for eye tracking
        window.addEventListener('mousemove', handleMouseMove);
        widgetElement = document.querySelector('.eye-widget');
        
        return () => {
            window.removeEventListener('mouseup', handleGlobalMouseUp);
            window.removeEventListener('mousemove', handleGlobalMouseMove);
            window.removeEventListener('keydown', handleKeydown);
            window.removeEventListener('mousemove', handleMouseMove);
        };
    });
    
    onDestroy(() => {
        if (bridge) {
            // Save conversation to memory if needed
            if (persistToMemory && messages.length > 0) {
                saveConversationToMemory();
            }
            
            // Clean up event listeners
            bridge.off('query_response', handleQueryResponse);
            bridge.off('memory_status', handleMemoryStatus);
            bridge.off('system_message', handleSystemMessage);
        }
    });
    
    function setupBridge() {
        try {
            bridge = new Bridge();
            
            // Register message handlers
            bridge.on('query_response', handleQueryResponse);
            bridge.on('memory_status', handleMemoryStatus);
            bridge.on('system_message', handleSystemMessage);
            bridge.on('sensor_data', handleSensorData);
            bridge.on('connection_status', handleConnectionStatus);
            
            // Connect to the backend
            isConnecting = true;
            bridge.connect().then(() => {
                isConnecting = false;
                connectionStatus = 'connected';
            }).catch(error => {
                console.error('Failed to connect:', error);
                isConnecting = false;
                connectionStatus = 'error';
                addSystemMessage('Failed to connect to the server. Please try again.', 'error');
            });
        } catch (error) {
            console.error('Error setting up bridge:', error);
            connectionStatus = 'error';
            addSystemMessage('Failed to initialize the connection.', 'error');
        }
    }
    
    function handleKeydown(event) {
        // Escape to close expanded widget
        if (event.key === 'Escape' && !isMinimized) {
            minimizeWidget();
        }
        
        // Ctrl+Alt+E to toggle widget
        if (event.ctrlKey && event.altKey && event.key === 'e') {
            toggleWidget();
        }

        // Enter to send message (only in chat input)
        if (event.key === 'Enter' && !event.shiftKey && event.target.classList.contains('message-input')) {
            event.preventDefault();
            sendMessage();
        }
    }
    
    function handleConnectionStatus(status) {
        connectionStatus = status.state || 'disconnected';
    }
    
    function handleQueryResponse(payload) {
        // Remove thinking indicator
        isThinking = false;
        
        // Add the response to messages
        addMessage('assistant', payload.response);
    }
    
    function handleMemoryStatus(payload) {
        const { connected, last_saved, success } = payload;
        if (success) {
            console.log('Memory operation successful. Last saved:', new Date(last_saved * 1000).toLocaleTimeString());
        }
    }
    
    function handleSystemMessage(payload) {
        const { message, severity } = payload;
        
        if (severity === 'error' || severity === 'important') {
            addSystemMessage(message, severity);
        }
    }
    
    function handleSensorData(data) {
        sensorData = data;
    }
    
    function addMessage(role, content) {
        const timestamp = new Date().toLocaleTimeString();
        
        // Add to messages array
        messages = [...messages, { role, content, timestamp }];
        
        // Auto-scroll to bottom
        setTimeout(() => {
            const messagesDiv = document.querySelector('.messages');
            if (messagesDiv) {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }, 0);
        
        // Save conversation to memory if enabled
        if (persistToMemory) {
            saveConversationToMemory();
        }
    }
    
    function addSystemMessage(message, severity = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        
        // Add to messages array
        messages = [...messages, { 
            role: 'system', 
            content: message, 
            timestamp,
            severity
        }];
        
        // Auto-scroll to bottom
        setTimeout(() => {
            const messagesDiv = document.querySelector('.messages');
            if (messagesDiv) {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }, 0);
    }
    
    async function sendMessage() {
        const text = userInput.trim();
        if (!text || connectionStatus !== 'connected' || isThinking) {
            return;
        }
        
        // Add user message
        addMessage('user', text);
        
        // Clear input and show thinking indicator
        userInput = '';
        isThinking = true;
        
        try {
            // Send to server
            await bridge.send('user_interaction', {
                type: 'query',
                query: text,
                request_id: generateId(),
                conversation_id: getConversationId(),
                timestamp: Date.now()
            });
        } catch (error) {
            console.error('Error sending message:', error);
            isThinking = false;
            addSystemMessage('Failed to send message. Please try again.', 'error');
        }
    }
    
    function clearConversation() {
        messages = [];
        
        // Notify server
        bridge.send('clear_conversation', {
            timestamp: Date.now()
        });
    }
    
    async function saveConversationToMemory() {
        if (!bridge || messages.length === 0) return;
        
        bridge.send('memory_store', {
            conversation: messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: Date.now()
            })),
            timestamp: Date.now()
        });
    }
    
    function toggleMemoryPersistence() {
        persistToMemory = !persistToMemory;
        
        if (persistToMemory) {
            saveConversationToMemory();
        }
    }
    
    function toggleScreenViewer() {
        showScreenViewer = !showScreenViewer;
    }
    
    function handleScreenViewerClose() {
        showScreenViewer = false;
    }
    
    function toggleWidget() {
        console.log('Toggling widget:', { isMinimized, isExpanded }); // Debug log
        if (isMinimized) {
            isMinimized = false;
            isExpanded = true;
            notificationCount = 0; // Clear notifications when expanding
        } else {
            isExpanded = !isExpanded;
        }
        console.log('Widget state after toggle:', { isMinimized, isExpanded }); // Debug log
    }
    
    function minimizeWidget() {
        console.log('Minimizing widget'); // Debug log
        isMinimized = true;
        isExpanded = false;
    }
    
    async function toggleInteraction() {
        isInteractive = !isInteractive;
        onToggleInteraction(isInteractive);
        
        // Also toggle interaction via Tauri bridge
        try {
            await bridge.toggleInteraction(isInteractive);
        } catch (e) {
            console.error('Error toggling interaction:', e);
        }
    }
    
    // Drag handling
    function startDrag(event) {
        dragging = true;
        dragOffsetX = event.clientX - widgetX;
        dragOffsetY = event.clientY - widgetY;
    }
    
    function handleGlobalMouseMove(event) {
        if (dragging) {
            let newX = event.clientX - dragOffsetX;
            let newY = event.clientY - dragOffsetY;
            // Clamp to viewport (assuming widget is 60x60px)
            const widgetWidth = 60;
            const widgetHeight = 60;
            newX = Math.max(0, Math.min(window.innerWidth - widgetWidth, newX));
            newY = Math.max(0, Math.min(window.innerHeight - widgetHeight, newY));
            widgetX = newX;
            widgetY = newY;
            // Save position to localStorage
            try {
                localStorage.setItem('eyeWidgetPosition', JSON.stringify({ x: widgetX, y: widgetY }));
            } catch (e) {
                console.error('Could not save position:', e);
            }
        }
    }
    
    function handleGlobalMouseUp() {
        if (dragging) {
            dragging = false;
        }
    }
    
    function handleMouseMove(event) {
        if (!widgetElement) return;
        
        const rect = widgetElement.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        // Calculate angle between mouse and widget center
        const deltaX = event.clientX - centerX;
        const deltaY = event.clientY - centerY;
        const angle = Math.atan2(deltaY, deltaX);
        eyeRotation = angle * (180 / Math.PI);
        
        // Calculate distance for scale effect
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const maxDistance = 300;
        const normalizedDistance = Math.min(distance / maxDistance, 1);
        
        // Update scale and glow based on distance
        eyeScale = 1 + (1 - normalizedDistance) * 0.2;
        glowIntensity = 1 - normalizedDistance;
        
        // Update pupil position
        const maxPupilOffset = 8; // Maximum pixels the pupil can move
        const pupilOffsetX = (deltaX / maxDistance) * maxPupilOffset;
        const pupilOffsetY = (deltaY / maxDistance) * maxPupilOffset;
        
        // Update CSS variables
        widgetElement.style.setProperty('--pupil-offset-x', `${pupilOffsetX}px`);
        widgetElement.style.setProperty('--pupil-offset-y', `${pupilOffsetY}px`);
    }
    
    // Utility functions
    function generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    function getConversationId() {
        if (!window.conversationId) {
            window.conversationId = generateId();
        }
        return window.conversationId;
    }
    
    function handleInput(event) {
        // Auto-resize textarea
        const textarea = event.target;
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    // Handle widget click
    function handleWidgetClick(event) {
        if (!dragging) {
            dispatch('click');
        }
    }
</script>

<div 
    class="eye-widget {connectionStatus} {isMinimized ? 'minimized' : ''}"
    style="left: {widgetX}px; top: {widgetY}px; --eye-rotation: {eyeRotation}deg; --eye-scale: {eyeScale}; --glow-intensity: {glowIntensity};"
    on:mousedown={startDrag}
    on:click={handleWidgetClick}
>
    <div class="widget-content">
        <div class="eye-container">
            <div class="eye-outer">
                <div class="eye-inner">
                    <div class="pupil">
                        <div class="pupil-core"></div>
                    </div>
                </div>
            </div>
            <div class="glow-effect"></div>
        </div>
        {#if notificationCount > 0}
            <div class="notification-badge">{notificationCount}</div>
        {/if}
        {#if connectionStatus === 'connected'}
            <div class="connection-indicator connected"></div>
        {:else if connectionStatus === 'error'}
            <div class="connection-indicator error"></div>
        {:else}
            <div class="connection-indicator connecting"></div>
        {/if}
    </div>
    
    <!-- Screen Viewer Modal -->
    {#if showScreenViewer}
        <div class="screen-viewer-modal">
            <div class="screen-viewer-container">
                <ScreenViewer 
                    on:close={handleScreenViewerClose}
                    bridgeService={bridge}
                />
            </div>
        </div>
    {/if}
</div>

<style>
    /* Base Styles */
    :global(body) {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        background: transparent !important;
    }
    
    .eye-widget-container {
        position: fixed;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        transition: transform 0.3s ease;
    }

    .eye-widget-container.minimized .chat-panel {
        display: none !important;
    }

    .eye-widget-container.expanded .chat-panel {
        display: flex !important;
    }
    
    /* Eye Icon */
    .eye-widget {
        position: fixed;
        width: 60px;
        height: 60px;
        background: #f0f0f0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: auto;
        overflow: hidden;
        animation: blink 4s infinite;
        transform-style: preserve-3d;
        perspective: 1000px;
    }
    
    .eye-widget:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 24px rgba(168, 85, 247, 0.3);
    }
    
    .eye-widget:active {
        transform: scale(0.95);
    }
    
    .widget-content {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .eye-container {
        position: relative;
        width: 40px;
        height: 40px;
        transform: scale(var(--eye-scale));
        transition: transform 0.2s ease-out;
    }
    
    .eye-outer {
        position: absolute;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
        border-radius: 50%;
        overflow: hidden;
        box-shadow: 
            inset 0 0 10px rgba(0, 0, 0, 0.1),
            inset 0 0 20px rgba(0, 0, 0, 0.05);
        transform-style: preserve-3d;
    }
    
    .eye-inner {
        position: absolute;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at 30% 30%, 
            #a855f7 0%,
            #7c3aed 50%,
            #4c1d95 100%);
        border-radius: 50%;
        transform: scale(0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: irisPulse 4s infinite;
        transform-style: preserve-3d;
    }
    
    /* Enhanced iris pattern */
    .eye-inner::before {
        content: '';
        position: absolute;
        width: 200%;
        height: 200%;
        background: 
            repeating-radial-gradient(
                circle at center,
                transparent 0,
                transparent 10px,
                rgba(255, 255, 255, 0.1) 10px,
                rgba(255, 255, 255, 0.1) 20px
            ),
            repeating-conic-gradient(
                from 0deg,
                transparent 0deg,
                transparent 10deg,
                rgba(255, 255, 255, 0.05) 10deg,
                rgba(255, 255, 255, 0.05) 20deg
            );
        animation: irisRotate 20s linear infinite;
        transform-style: preserve-3d;
    }
    
    /* Add iris texture overlay */
    .eye-inner::after {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background: url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100' height='100' filter='url(%23noise)' opacity='0.1'/%3E%3C/svg%3E");
        opacity: 0.1;
        mix-blend-mode: overlay;
    }
    
    .pupil {
        position: absolute;
        width: 20px;
        height: 20px;
        background: radial-gradient(circle at 30% 30%, #000, #111);
        border-radius: 50%;
        transform: translate(
            calc(var(--pupil-offset-x, 0px)),
            calc(var(--pupil-offset-y, 0px))
        ) scale(var(--pupil-scale, 1));
        transition: transform 0.1s cubic-bezier(0.4, 0, 0.2, 1);
        animation: pupilPulse 4s infinite;
        box-shadow: 
            inset 0 0 10px rgba(0, 0, 0, 0.5),
            0 0 5px rgba(0, 0, 0, 0.3);
    }
    
    .pupil-core {
        position: absolute;
        width: 8px;
        height: 8px;
        background: radial-gradient(circle at 30% 30%, #fff, #ddd);
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 
            0 0 4px rgba(255, 255, 255, 0.8),
            0 0 8px rgba(255, 255, 255, 0.4);
    }
    
    /* Enhanced pupil highlight */
    .pupil-core::after {
        content: '';
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        top: 20%;
        left: 20%;
        box-shadow: 0 0 2px rgba(255, 255, 255, 0.6);
    }
    
    .glow-effect {
        position: absolute;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at center, 
            rgba(168, 85, 247, calc(0.2 * var(--glow-intensity))) 0%,
            rgba(168, 85, 247, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
        animation: glowPulse 4s infinite;
        mix-blend-mode: screen;
    }
    
    /* Enhanced eyelid */
    .eye-widget::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 50%;
        background: linear-gradient(to bottom,
            #f0f0f0 0%,
            #e0e0e0 100%);
        border-radius: 50% 50% 0 0;
        transform-origin: bottom;
        animation: eyelidBlink 4s infinite;
        z-index: 2;
        box-shadow: 
            inset 0 2px 4px rgba(0, 0, 0, 0.1),
            inset 0 -1px 2px rgba(255, 255, 255, 0.5);
    }
    
    /* Multiple reflections */
    .eye-widget::after {
        content: '';
        position: absolute;
        top: 20%;
        left: 20%;
        width: 15px;
        height: 15px;
        background: radial-gradient(circle at 30% 30%, 
            rgba(255, 255, 255, 0.9),
            rgba(255, 255, 255, 0.6));
        border-radius: 50%;
        z-index: 3;
        animation: reflectionMove 4s infinite;
        box-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
    }
    
    /* Secondary reflection */
    .eye-widget::before {
        content: '';
        position: absolute;
        top: 30%;
        left: 40%;
        width: 8px;
        height: 8px;
        background: radial-gradient(circle at 30% 30%, 
            rgba(255, 255, 255, 0.8),
            rgba(255, 255, 255, 0.4));
        border-radius: 50%;
        z-index: 3;
        animation: reflectionMove 4s infinite reverse;
        box-shadow: 0 0 3px rgba(255, 255, 255, 0.3);
    }
    
    .connection-indicator {
        position: absolute;
        bottom: 5px;
        right: 5px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ccc;
        box-shadow: 0 0 8px currentColor;
    }
    
    .connection-indicator.connected {
        background: #a855f7;
        background: #22c55e;
        animation: pulse 2s infinite;
    }
    
    .connection-indicator.error {
        background: #ef4444;
        animation: error-pulse 1s infinite;
    }
    
    .connection-indicator.connecting {
        background: #f59e0b;
        animation: connecting-pulse 1.5s infinite;
    }
    
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #ef4444;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        animation: badge-pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.1); }
        100% { opacity: 0.6; transform: scale(1); }
    }
    
    @keyframes error-pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    @keyframes connecting-pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes badge-pulse {
        0% { transform: scale(1); box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
        50% { transform: scale(1.1); box-shadow: 0 0 15px rgba(239, 68, 68, 0.7); }
        100% { transform: scale(1); box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
    }
    
    @keyframes blink {
        0%, 96%, 100% { transform: scaleY(1); }
        98% { transform: scaleY(0.1); }
    }
    
    @keyframes eyelidBlink {
        0%, 96%, 100% { transform: scaleY(0); }
        98% { transform: scaleY(1); }
    }
    
    @keyframes irisPulse {
        0%, 100% { transform: scale(0.8); }
        50% { transform: scale(0.85); }
    }
    
    @keyframes pupilPulse {
        0%, 100% { 
            transform: scale(1) translate(var(--pupil-offset-x), var(--pupil-offset-y));
            filter: brightness(1);
        }
        50% { 
            transform: scale(0.9) translate(var(--pupil-offset-x), var(--pupil-offset-y));
            filter: brightness(1.2);
        }
    }
    
    @keyframes glowPulse {
        0%, 100% { 
            opacity: 0.6;
            transform: scale(1);
        }
        50% { 
            opacity: 1;
            transform: scale(1.05);
        }
    }
    
    @keyframes reflectionMove {
        0% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(2px, 2px) scale(1.1); }
        50% { transform: translate(0, 0) scale(1); }
        75% { transform: translate(-2px, -2px) scale(0.9); }
        100% { transform: translate(0, 0) scale(1); }
    }
    
    @keyframes irisRotate {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.1); }
        100% { transform: rotate(360deg) scale(1); }
    }
    
    /* Chat Panel */
    .chat-panel {
        width: 380px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin-top: 10px;
        display: flex;
        flex-direction: column;
        max-height: 85vh;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(5px);
    }
    
    .title-area {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .title-area h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        background: linear-gradient(135deg, #2c3e50, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 0.5px;
    }
    
    .connection-badge {
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 20px;
        background: rgba(0, 0, 0, 0.05);
        color: #666;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .connection-badge.connected {
        background: rgba(46, 213, 115, 0.15);
        color: #2ed573;
    }
    
    .connection-badge.error {
        background: rgba(255, 71, 87, 0.15);
        color: #ff4757;
    }
    
    .header-actions {
        display: flex;
        gap: 10px;
    }
    
    .icon-button {
        background: rgba(0, 0, 0, 0.05);
        border: none;
        cursor: pointer;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: #2c3e50;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .icon-button:hover {
        background: rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    .minimize-icon {
        font-size: 18px;
        line-height: 1;
        position: relative;
        top: -3px;
    }
    
    .messages {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        min-height: 200px;
        max-height: 500px;
        background: rgba(255, 255, 255, 0.5);
    }
    
    .messages::-webkit-scrollbar {
        width: 6px;
    }
    
    .messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .messages::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 10px;
    }
    
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin: 40px 0;
        color: #2c3e50;
        padding: 20px;
    }
    
    .empty-state p {
        margin: 8px 0;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .hint {
        font-size: 13px;
        color: #7f8c8d;
        margin-top: 12px;
        font-style: italic;
    }
    
    .message {
        display: flex;
        gap: 12px;
        animation: messageSlide 0.3s ease;
        padding: 12px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .message:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .message.user {
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
        margin-left: 20px;
    }
    
    .message.assistant {
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.1), rgba(39, 174, 96, 0.1));
        margin-right: 20px;
    }
    
    .message.error {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(192, 57, 43, 0.1));
    }
    
    .message-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    /* Add eye widget to assistant messages */
    .message.assistant .message-avatar {
        background: #f0f0f0;
        transform-style: preserve-3d;
        perspective: 1000px;
    }

    .message.assistant .message-avatar::before {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
        border-radius: 50%;
        overflow: hidden;
        box-shadow: 
            inset 0 0 10px rgba(0, 0, 0, 0.1),
            inset 0 0 20px rgba(0, 0, 0, 0.05);
    }

    .message.assistant .message-avatar::after {
        content: '';
        position: absolute;
        width: 70%;
        height: 70%;
        top: 15%;
        left: 15%;
        background: radial-gradient(circle at 30% 30%, 
            #a855f7 0%,
            #7c3aed 50%,
            #4c1d95 100%);
        border-radius: 50%;
        animation: irisPulse 4s infinite;
    }

    /* Add iris pattern to assistant avatar */
    .message.assistant .message-avatar .iris-pattern {
        position: absolute;
        width: 200%;
        height: 200%;
        top: -50%;
        left: -50%;
        background: 
            repeating-radial-gradient(
                circle at center,
                transparent 0,
                transparent 10px,
                rgba(255, 255, 255, 0.1) 10px,
                rgba(255, 255, 255, 0.1) 20px
            ),
            repeating-conic-gradient(
                from 0deg,
                transparent 0deg,
                transparent 10deg,
                rgba(255, 255, 255, 0.05) 10deg,
                rgba(255, 255, 255, 0.05) 20deg
            );
        animation: irisRotate 20s linear infinite;
        z-index: 1;
    }

    /* Add pupil to assistant avatar */
    .message.assistant .message-avatar .pupil {
        position: absolute;
        width: 40%;
        height: 40%;
        top: 30%;
        left: 30%;
        background: radial-gradient(circle at 30% 30%, #000, #111);
        border-radius: 50%;
        box-shadow: 
            inset 0 0 10px rgba(0, 0, 0, 0.5),
            0 0 5px rgba(0, 0, 0, 0.3);
        z-index: 2;
    }

    /* Add pupil highlight to assistant avatar */
    .message.assistant .message-avatar .pupil::after {
        content: '';
        position: absolute;
        width: 30%;
        height: 30%;
        top: 20%;
        left: 20%;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        box-shadow: 0 0 2px rgba(255, 255, 255, 0.6);
    }

    /* Add reflection to assistant avatar */
    .message.assistant .message-avatar .reflection {
        position: absolute;
        width: 30%;
        height: 30%;
        top: 20%;
        left: 20%;
        background: radial-gradient(circle at 30% 30%, 
            rgba(255, 255, 255, 0.9),
            rgba(255, 255, 255, 0.6));
        border-radius: 50%;
        z-index: 3;
        box-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
    }

    /* Add secondary reflection to assistant avatar */
    .message.assistant .message-avatar .reflection-secondary {
        position: absolute;
        width: 15%;
        height: 15%;
        top: 30%;
        left: 40%;
        background: radial-gradient(circle at 30% 30%, 
            rgba(255, 255, 255, 0.8),
            rgba(255, 255, 255, 0.4));
        border-radius: 50%;
        z-index: 3;
        box-shadow: 0 0 3px rgba(255, 255, 255, 0.3);
    }

    /* Update message content wrapper */
    .message-content-wrapper {
        flex: 1;
        min-width: 0;
        position: relative;
        z-index: 1;
    }

    /* Add glow effect to assistant messages */
    .message.assistant::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at center, 
            rgba(168, 85, 247, 0.1) 0%,
            rgba(168, 85, 247, 0) 70%);
        border-radius: 12px;
        pointer-events: none;
        animation: glowPulse 4s infinite;
        mix-blend-mode: screen;
    }

    /* Dark mode support for messages */
    @media (prefers-color-scheme: dark) {
        .message.assistant .message-avatar {
            background: #e0e0e0;
        }
        
        .message.assistant .message-avatar::before {
            background: linear-gradient(135deg, #e0e0e0, #d0d0d0);
        }
        
        .message.assistant .message-avatar::after {
            background: radial-gradient(circle at 30% 30%, 
                #7c3aed 0%,
                #6d28d9 50%,
                #4c1d95 100%);
        }
    }
    
    .input-area {
        padding: 15px 20px;
        background: rgba(255, 255, 255, 0.9);
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        display: flex;
        gap: 10px;
        align-items: flex-end;
    }
    
    .message-input {
        flex: 1;
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        padding: 12px 15px;
        font-size: 14px;
        line-height: 1.5;
        resize: none;
        background: rgba(255, 255, 255, 0.9);
        transition: all 0.3s ease;
        max-height: 120px;
        min-height: 24px;
    }
    
    .message-input:focus {
        outline: none;
        border-color: #3498db;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }
    
    .send-button {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        font-size: 18px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .send-button:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
    }
    
    .send-button:disabled {
        background: #bdc3c7;
        cursor: not-allowed;
    }
    
    .panel-footer {
        padding: 12px 20px;
        background: rgba(255, 255, 255, 0.9);
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        display: flex;
        justify-content: space-between;
        gap: 10px;
    }
    
    .footer-button {
        flex: 1;
        padding: 8px 15px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.9);
        color: #2c3e50;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .footer-button:hover {
        background: rgba(0, 0, 0, 0.05);
        transform: translateY(-1px);
    }
    
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .thinking-indicator {
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: center;
        padding: 8px;
    }
    
    .thinking-indicator .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3498db;
        animation: thinking 1.4s infinite ease-in-out;
    }
    
    .thinking-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
    .thinking-indicator .dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes thinking {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .eye-widget {
            background: #e0e0e0;
        }
        
        .eye-outer {
            background: linear-gradient(135deg, #e0e0e0, #d0d0d0);
        }
        
        .eye-inner {
            background: radial-gradient(circle at 30% 30%, 
                #7c3aed 0%,
                #6d28d9 50%,
                #4c1d95 100%);
        }
        
        .eye-widget::before {
            background: linear-gradient(to bottom,
                #e0e0e0 0%,
                #d0d0d0 100%);
        }
        
        .chat-panel {
            background-color: #292929;
            color: #e0e0e0;
        }
        
        .panel-header {
            background-color: #333;
            border-color: #444;
        }
        
        .title-area h3 {
            color: #e0e0e0;
        }
        
        .connection-badge {
            background-color: #444;
            color: #ccc;
        }
        
        .connection-badge.connected {
            background-color: #2e3e33;
            color: #8bc34a;
        }
        
        .connection-badge.error {
            background-color: #3e2c2c;
            color: #ff8a8a;
        }
        
        .message.user .message-content {
            background-color: #0d47a1;
            color: white;
        }
        
        .message.assistant .message-content {
            background-color: #3a3a3a;
            color: #e0e0e0;
        }
        
        .message.system .message-content {
            background-color: #4d3319;
            color: #ffd180;
        }
        
        .message-input {
            background-color: #333;
            color: #e0e0e0;
            border-color: #555;
        }
        
        .message-input:focus {
            border-color: #6dbd6d;
        }
        
        .icon-button {
            color: #ccc;
        }
        
        .icon-button:hover {
            background-color: #444;
        }
        
        .footer-button {
            background-color: #444;
            color: #e0e0e0;
        }
        
        .footer-button:hover {
            background-color: #555;
        }
    }

    .widget-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        justify-content: flex-start;
        align-items: center;
        z-index: 9998;
        pointer-events: none;
        background: transparent;
    }

    .widget {
        position: relative;
        width: 60px;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.3s ease;
        margin-left: 20px;
    }

    .widget-icon {
        font-size: 48px;
        opacity: 0.3;
        transition: all 0.3s ease;
    }

    .widget:hover .widget-icon {
        opacity: 0.8;
        transform: scale(1.1);
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .widget-icon {
            opacity: 0.2;
        }
        
        .widget:hover .widget-icon {
            opacity: 0.7;
        }
    }

    /* Screen Viewer Modal Styles */
    .screen-viewer-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: modalFadeIn 0.3s ease;
    }

    .screen-viewer-container {
        position: relative;
        max-width: 95vw;
        max-height: 95vh;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 16px 64px rgba(0, 0, 0, 0.3);
        animation: modalSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes modalFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes modalSlideIn {
        from { 
            opacity: 0; 
            transform: scale(0.9) translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: scale(1) translateY(0); 
        }
    }
</style>