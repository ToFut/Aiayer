<script>
    import { onMount, onDestroy } from 'svelte';
    import { Bridge } from '../services/bridge';
    
    let bridge;
    let isExpanded = false;
    let isInteractive = false;
    let showControls = false;
    let userInput = '';
    let messages = [];
    let connectionStatus = 'disconnected';
    let isConnecting = false;
    let transformInterface;
    
    onMount(() => {
        setupBridge();
        
        // Handle window resize
        window.addEventListener('resize', handleResize);
        
        // Handle mouse movement for controls
        window.addEventListener('mousemove', handleMouseMove);
        
        // Handle connection events
        window.addEventListener('bridge-connected', handleBridgeConnected);
        window.addEventListener('bridge-disconnected', handleBridgeDisconnected);
        window.addEventListener('bridge-error', handleBridgeError);
        
        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('bridge-connected', handleBridgeConnected);
            window.removeEventListener('bridge-disconnected', handleBridgeDisconnected);
            window.removeEventListener('bridge-error', handleBridgeError);
        };
    });
    
    onDestroy(() => {
        // Clean up event listeners to prevent memory leaks
        if (bridge) {
            bridge.off('query_response', handleQueryResponse);
            bridge.off('transform-interface', handleTransformation);
        }
    });
    
    function setupBridge() {
        bridge = new Bridge();
        
        // Register message handlers
        bridge.on('query_response', handleQueryResponse);
        bridge.on('transform-interface', handleTransformation);
        bridge.on('connection_status', handleConnectionStatus);
        
        // Connect to the backend
        isConnecting = true;
        bridge.connect().then(() => {
            isConnecting = false;
        }).catch(error => {
            console.error('Failed to connect:', error);
            isConnecting = false;
        });
    }
    
    function handleBridgeConnected() {
        connectionStatus = 'connected';
        console.log('Bridge connected');
    }
    
    function handleBridgeDisconnected() {
        connectionStatus = 'disconnected';
        console.log('Bridge disconnected');
    }
    
    function handleBridgeError(event) {
        connectionStatus = 'error';
        console.error('Bridge error:', event.detail);
    }
    
    function handleConnectionStatus(status) {
        connectionStatus = status.state;
    }
    
    function handleResize() {
        // Update canvas size if transformInterface exists
        if (transformInterface && typeof transformInterface.updateLayout === 'function') {
            transformInterface.updateLayout();
        }
    }
    
    function handleMouseMove(event) {
        if (event.clientY < 20) {
            showControls = true;
        } else if (event.clientY > 150 && showControls) {
            showControls = false;
        }
    }
    
    function toggleExpanded() {
        isExpanded = !isExpanded;
    }
    
    async function toggleInteraction() {
        isInteractive = !isInteractive;
        
        // Update interactivity in transform interface if it exists
        if (transformInterface && typeof transformInterface.setInteractive === 'function') {
            transformInterface.setInteractive(isInteractive);
        }
        
        // Toggle interaction via Tauri bridge
        await bridge.toggleInteraction(isInteractive);
    }
    
    function handleQueryResponse(response) {
        // Add the response to messages
        messages = [...messages, {
            type: 'assistant',
            content: response.response
        }];
        
        // Auto-scroll to bottom
        setTimeout(() => {
            const messagesDiv = document.querySelector('.messages');
            if (messagesDiv) {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }, 0);
    }
    
    function handleTransformation(data) {
        // Handle interface transformation
        console.log('Transformation data:', data);
        
        // Apply transformation if the interface component exists
        if (transformInterface && typeof transformInterface.updateLayout === 'function') {
            transformInterface.updateLayout(data.layout, data.interactionMap || {});
        }
    }
    
    async function sendQuery() {
        if (!userInput.trim() || connectionStatus !== 'connected') return;
        
        // Add user message to the conversation
        messages = [...messages, {
            type: 'user',
            content: userInput
        }];
        
        // Send the query to the backend
        bridge.send('user_interaction', {
            type: 'query',
            query: userInput
        });
        
        // Clear input field
        userInput = '';
        
        // Auto-scroll to bottom
        setTimeout(() => {
            const messagesDiv = document.querySelector('.messages');
            if (messagesDiv) {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }, 0);
    }
    
    function clearConversation() {
        messages = [];
    }
    
    function requestTransformation() {
        bridge.send('transform_request', {
            preferences: {
                simplifyUI: true,
                highlight: true
            }
        });
    }
</script>

<div class="assistant-widget" class:expanded={isExpanded} class:connecting={isConnecting} class:connected={connectionStatus === 'connected'} class:error={connectionStatus === 'error'}>
    <button 
        class="widget-icon" 
        on:click={toggleExpanded}
        on:keydown={(e) => e.key === 'Enter' && toggleExpanded()}
        aria-label="Toggle assistant widget"
    >
        <span>🤖</span>
        <span class="connection-status" title={connectionStatus}></span>
    </button>
    
    {#if isExpanded}
        <div class="widget-content">
            <div class="widget-header">
                <h3>AI Assistant</h3>
                <div class="connection-badge" class:connecting={isConnecting} class:connected={connectionStatus === 'connected'} class:error={connectionStatus === 'error'}>
                    {#if isConnecting}
                        Connecting...
                    {:else if connectionStatus === 'connected'}
                        Connected
                    {:else if connectionStatus === 'error'}
                        Connection Error
                    {:else}
                        Disconnected
                    {/if}
                </div>
                <button class="close-button" on:click={toggleExpanded}>×</button>
            </div>
            
            <div class="messages">
                {#if messages.length === 0}
                    <div class="empty-state">
                        <p>Ask me anything about what you're working on!</p>
                    </div>
                {:else}
                    {#each messages as message}
                        <div class="message {message.type}">
                            <div class="message-content">{message.content}</div>
                        </div>
                    {/each}
                {/if}
            </div>
            
            <div class="input-area">
                <input
                    type="text"
                    bind:value={userInput}
                    on:keydown={(e) => e.key === 'Enter' && sendQuery()}
                    placeholder="Type your message..."
                    aria-label="Message input"
                    disabled={connectionStatus !== 'connected'}
                />
                <button 
                    class="send-button"
                    on:click={sendQuery}
                    on:keydown={(e) => e.key === 'Enter' && sendQuery()}
                    aria-label="Send message"
                    disabled={connectionStatus !== 'connected'}
                >
                    Send
                </button>
            </div>
            
            <div class="actions">
                <button class="action-button" on:click={clearConversation}>Clear Chat</button>
                <button class="action-button" on:click={requestTransformation}>Transform UI</button>
            </div>
        </div>
    {/if}
    
    {#if showControls || isExpanded}
        <div class="controls">
            <button
                class="control-button"
                class:active={isInteractive}
                on:click={toggleInteraction}
                title={isInteractive ? 'Disable Interaction' : 'Enable Interaction'}
            >
                {isInteractive ? '🔒' : '🖱️'}
            </button>
        </div>
    {/if}
</div>

<style>
    .assistant-widget {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }
    
    .widget-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #4CAF50;
        border-radius: 50%;
        cursor: pointer;
        border: none;
        padding: 0;
        margin: 10px;
        position: relative;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, background-color 0.2s ease;
    }
    
    .widget-icon:hover {
        transform: scale(1.05);
    }
    
    .widget-icon span {
        font-size: 24px;
        color: white;
    }
    
    .connection-status {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #999;
        border: 2px solid white;
    }
    
    .connecting .connection-status {
        background-color: #FFC107;
        animation: pulse 1.5s infinite;
    }
    
    .connected .connection-status {
        background-color: #4CAF50;
    }
    
    .error .connection-status {
        background-color: #F44336;
    }
    
    @keyframes pulse {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }
    
    .widget-content {
        padding: 0;
        width: 350px;
        max-height: 600px;
        display: flex;
        flex-direction: column;
        border-radius: 12px;
        overflow: hidden;
    }
    
    .widget-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px;
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;
    }
    
    .widget-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
    }
    
    .connection-badge {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 12px;
        background-color: #e0e0e0;
        color: #666;
    }
    
    .connection-badge.connecting {
        background-color: #FFF8E1;
        color: #FF8F00;
    }
    
    .connection-badge.connected {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    
    .connection-badge.error {
        background-color: #FFEBEE;
        color: #C62828;
    }
    
    .close-button {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
        padding: 0;
        margin-left: 10px;
    }
    
    .messages {
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-height: 350px;
    }
    
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100px;
        color: #666;
        text-align: center;
        font-style: italic;
    }
    
    .message {
        max-width: 85%;
        padding: 12px 16px;
        border-radius: 18px;
        position: relative;
        word-wrap: break-word;
        line-height: 1.5;
    }
    
    .message.user {
        background-color: #E3F2FD;
        color: #0D47A1;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }
    
    .message.assistant {
        background-color: #F5F5F5;
        color: #333;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    
    .message-content {
        font-size: 14px;
    }
    
    .input-area {
        display: flex;
        gap: 10px;
        padding: 15px;
        border-top: 1px solid #eee;
    }
    
    input {
        flex: 1;
        padding: 12px 16px;
        border: 1px solid #ddd;
        border-radius: 24px;
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s ease;
    }
    
    input:focus {
        border-color: #4CAF50;
    }
    
    input:disabled {
        background-color: #f5f5f5;
        cursor: not-allowed;
    }
    
    .send-button {
        padding: 0 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 24px;
        cursor: pointer;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }
    
    .send-button:hover {
        background-color: #45a049;
    }
    
    .send-button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }
    
    .actions {
        display: flex;
        padding: 10px 15px 15px;
        gap: 10px;
        justify-content: space-between;
    }
    
    .action-button {
        flex: 1;
        padding: 8px 0;
        background-color: #f0f0f0;
        color: #333;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.2s ease;
    }
    
    .action-button:hover {
        background-color: #e0e0e0;
    }
    
    .controls {
        position: absolute;
        top: 0;
        left: -40px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 10px;
    }
    
    .control-button {
        width: 36px;
        height: 36px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    
    .control-button:hover {
        transform: scale(1.05);
    }
    
    .control-button.active {
        background: #4CAF50;
        color: white;
    }
</style>
