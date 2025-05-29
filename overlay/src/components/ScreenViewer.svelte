<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    import { Bridge } from '../services/bridge';
    
    // Create event dispatcher
    const dispatch = createEventDispatcher();
    
    // Props
    export let isVisible = false;
    export let bridge = null;
    
    // State
    let screenFrame = null;
    let isConnected = false;
    let fps = 0;
    let resolution = '0x0';
    let activeWindow = 'Unknown';
    let cursorPosition = { x: 0, y: 0 };
    let uiElements = [];
    let automationOverlay = null;
    let isScreenSharing = false;
    let viewerElement;
    
    // Performance tracking
    let framesReceived = 0;
    let lastFrameTime = 0;
    
    // Viewer settings
    let showUIElements = true;
    let showCursor = true;
    let showAutomationOverlay = true;
    let scaleFactor = 1.0;
    
    onMount(() => {
        setupEventListeners();
        
        // Auto-start screen sharing if visible
        if (isVisible && bridge) {
            startScreenSharing();
        }
    });
    
    onDestroy(() => {
        stopScreenSharing();
    });
    
    function setupEventListeners() {
        // Listen for screen frame updates
        window.addEventListener('screen-frame-received', handleScreenFrame);
        window.addEventListener('automation-overlay-update', handleAutomationOverlay);
        window.addEventListener('bridge-connected', handleBridgeConnected);
        window.addEventListener('bridge-disconnected', handleBridgeDisconnected);
    }
    
    function handleScreenFrame(event) {
        const frameData = event.detail;
        
        screenFrame = frameData;
        resolution = `${frameData.width}x${frameData.height}`;
        fps = frameData.fps || 0;
        activeWindow = frameData.active_window || 'Unknown';
        cursorPosition = frameData.cursor_position || { x: 0, y: 0 };
        uiElements = frameData.ui_elements || [];
        
        framesReceived++;
        lastFrameTime = Date.now();
        
        // Update viewer display
        updateScreenDisplay(frameData);
    }
    
    function handleAutomationOverlay(event) {
        automationOverlay = event.detail;
    }
    
    function handleBridgeConnected() {
        isConnected = true;
        if (isVisible) {
            startScreenSharing();
        }
    }
    
    function handleBridgeDisconnected() {
        isConnected = false;
        isScreenSharing = false;
    }
    
    function updateScreenDisplay(frameData) {
        const viewer = document.querySelector('.screen-viewer-image');
        if (viewer && frameData.data) {
            const imageUrl = `data:image/jpeg;base64,${frameData.data}`;
            viewer.src = imageUrl;
        }
    }
    
    function startScreenSharing() {
        if (bridge && isConnected && !isScreenSharing) {
            bridge.requestScreenSharing();
            isScreenSharing = true;
            console.log('Screen sharing requested');
        }
    }
    
    function stopScreenSharing() {
        if (bridge && isScreenSharing) {
            bridge.stopScreenSharing();
            isScreenSharing = false;
            console.log('Screen sharing stopped');
        }
    }
    
    function toggleUIElements() {
        showUIElements = !showUIElements;
    }
    
    function toggleCursor() {
        showCursor = !showCursor;
    }
    
    function toggleAutomationOverlay() {
        showAutomationOverlay = !showAutomationOverlay;
    }
    
    function handleZoomIn() {
        scaleFactor = Math.min(scaleFactor * 1.2, 3.0);
    }
    
    function handleZoomOut() {
        scaleFactor = Math.max(scaleFactor / 1.2, 0.3);
    }
    
    function handleResetZoom() {
        scaleFactor = 1.0;
    }
    
    // Update visibility
    $: if (isVisible && bridge && isConnected && !isScreenSharing) {
        startScreenSharing();
    } else if (!isVisible && isScreenSharing) {
        stopScreenSharing();
    }
</script>

{#if isVisible}
    <div class="screen-viewer-container" bind:this={viewerElement}>
        <!-- Header with controls -->
        <div class="viewer-header">
            <div class="viewer-info">
                <span class="connection-status {isConnected ? 'connected' : 'disconnected'}">
                    {isConnected ? '🟢' : '🔴'} {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                <span class="resolution">📺 {resolution}</span>
                <span class="fps">📊 {fps.toFixed(1)} FPS</span>
                <span class="active-window">🖼️ {activeWindow}</span>
            </div>
            
            <div class="viewer-controls">
                <button 
                    class="control-btn {showUIElements ? 'active' : ''}" 
                    on:click={toggleUIElements}
                    title="Toggle UI Elements"
                >
                    🎯
                </button>
                <button 
                    class="control-btn {showCursor ? 'active' : ''}" 
                    on:click={toggleCursor}
                    title="Toggle Cursor"
                >
                    🖱️
                </button>
                <button 
                    class="control-btn {showAutomationOverlay ? 'active' : ''}" 
                    on:click={toggleAutomationOverlay}
                    title="Toggle Automation Overlay"
                >
                    🤖
                </button>
                <button class="control-btn" on:click={handleZoomOut} title="Zoom Out">🔍-</button>
                <button class="control-btn" on:click={handleResetZoom} title="Reset Zoom">🔍</button>
                <button class="control-btn" on:click={handleZoomIn} title="Zoom In">🔍+</button>
                <button class="control-btn close-btn" on:click={() => dispatch('close')} title="Close">✕</button>
            </div>
        </div>
        
        <!-- Screen viewer -->
        <div class="screen-viewer" style="transform: scale({scaleFactor})">
            {#if screenFrame}
                <img 
                    class="screen-viewer-image" 
                    alt="Shared Screen"
                    draggable="false"
                />
                
                <!-- Cursor overlay -->
                {#if showCursor && cursorPosition}
                    <div 
                        class="cursor-overlay"
                        style="left: {cursorPosition.x}px; top: {cursorPosition.y}px"
                    ></div>
                {/if}
                
                <!-- UI Elements overlay -->
                {#if showUIElements}
                    <div class="ui-elements-overlay">
                        {#each uiElements as element}
                            {#if element.bounds && element.bounds.length >= 4}
                                <div 
                                    class="ui-element-overlay {element.type}"
                                    style="
                                        left: {element.bounds[0]}px; 
                                        top: {element.bounds[1]}px; 
                                        width: {element.bounds[2]}px; 
                                        height: {element.bounds[3]}px;
                                    "
                                    title="{element.text || element.type} (confidence: {(element.confidence * 100).toFixed(1)}%)"
                                >
                                    {#if element.text}
                                        <span class="element-label">{element.text}</span>
                                    {/if}
                                </div>
                            {/if}
                        {/each}
                    </div>
                {/if}
                
                <!-- Automation execution overlay -->
                {#if showAutomationOverlay}
                    <div class="automation-execution-overlay">
                        {#if automationOverlay && automationOverlay.target_position}
                            <div 
                                class="execution-indicator {automationOverlay.action}"
                                style="
                                    left: {automationOverlay.target_position.x}px; 
                                    top: {automationOverlay.target_position.y}px;
                                "
                            >
                                <div class="indicator-pulse"></div>
                                <span class="action-label">{automationOverlay.action.toUpperCase()}</span>
                            </div>
                        {/if}
                    </div>
                {/if}
            {:else}
                <div class="no-screen-message">
                    {#if !isConnected}
                        <div class="status-icon">🔌</div>
                        <h3>Not Connected</h3>
                        <p>Waiting for connection to screen sharing service...</p>
                    {:else if !isScreenSharing}
                        <div class="status-icon">📺</div>
                        <h3>Starting Screen Sharing</h3>
                        <p>Initializing real-time screen capture...</p>
                    {:else}
                        <div class="status-icon">⏳</div>
                        <h3>Loading Screen</h3>
                        <p>Waiting for first frame...</p>
                    {/if}
                </div>
            {/if}
        </div>
        
        <!-- Footer with statistics -->
        <div class="viewer-footer">
            <span class="stats">📦 Frames: {framesReceived}</span>
            <span class="stats">🔄 Scale: {(scaleFactor * 100).toFixed(0)}%</span>
            <span class="stats">🎯 UI Elements: {uiElements.length}</span>
            {#if automationOverlay}
                <span class="stats automation-status">🤖 {automationOverlay.action}: {automationOverlay.target}</span>
            {/if}
        </div>
    </div>
{/if}

<style>
    .screen-viewer-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(20, 20, 20, 0.95);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        z-index: 1000;
        max-width: 90vw;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        backdrop-filter: blur(10px);
    }
    
    .viewer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: rgba(40, 40, 40, 0.9);
        border-radius: 12px 12px 0 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .viewer-info {
        display: flex;
        gap: 16px;
        align-items: center;
        font-size: 12px;
        color: #e0e0e0;
    }
    
    .connection-status.connected {
        color: #4ade80;
    }
    
    .connection-status.disconnected {
        color: #ef4444;
    }
    
    .viewer-controls {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    
    .control-btn {
        background: rgba(60, 60, 60, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 6px 10px;
        color: #e0e0e0;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    .control-btn:hover {
        background: rgba(80, 80, 80, 0.9);
        border-color: rgba(255, 255, 255, 0.3);
    }
    
    .control-btn.active {
        background: rgba(168, 85, 247, 0.8);
        border-color: rgba(168, 85, 247, 0.6);
        color: white;
    }
    
    .control-btn.close-btn {
        background: rgba(239, 68, 68, 0.8);
        border-color: rgba(239, 68, 68, 0.6);
    }
    
    .control-btn.close-btn:hover {
        background: rgba(239, 68, 68, 1);
    }
    
    .screen-viewer {
        position: relative;
        overflow: auto;
        flex: 1;
        min-height: 400px;
        background: #000;
        transform-origin: center;
        transition: transform 0.2s ease;
    }
    
    .screen-viewer-image {
        display: block;
        max-width: 100%;
        height: auto;
        user-select: none;
    }
    
    .cursor-overlay {
        position: absolute;
        width: 20px;
        height: 20px;
        background: rgba(255, 255, 255, 0.8);
        border: 2px solid rgba(0, 0, 0, 0.8);
        border-radius: 50%;
        pointer-events: none;
        z-index: 10;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
    
    .ui-elements-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 5;
    }
    
    .ui-element-overlay {
        position: absolute;
        border: 2px solid rgba(74, 222, 128, 0.8);
        background: rgba(74, 222, 128, 0.1);
        pointer-events: none;
        transition: all 0.2s ease;
    }
    
    .ui-element-overlay.button {
        border-color: rgba(59, 130, 246, 0.8);
        background: rgba(59, 130, 246, 0.1);
    }
    
    .ui-element-overlay.input {
        border-color: rgba(245, 158, 11, 0.8);
        background: rgba(245, 158, 11, 0.1);
    }
    
    .ui-element-overlay.text {
        border-color: rgba(168, 85, 247, 0.8);
        background: rgba(168, 85, 247, 0.1);
    }
    
    .element-label {
        position: absolute;
        bottom: 100%;
        left: 0;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 2px 6px;
        font-size: 10px;
        border-radius: 4px;
        white-space: nowrap;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .automation-execution-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 15;
    }
    
    .execution-indicator {
        position: absolute;
        transform: translate(-50%, -50%);
        z-index: 20;
    }
    
    .indicator-pulse {
        width: 40px;
        height: 40px;
        background: rgba(239, 68, 68, 0.8);
        border-radius: 50%;
        animation: pulse 1s infinite;
    }
    
    .execution-indicator.click .indicator-pulse {
        background: rgba(59, 130, 246, 0.8);
    }
    
    .execution-indicator.type .indicator-pulse {
        background: rgba(245, 158, 11, 0.8);
    }
    
    .action-label {
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 4px;
        white-space: nowrap;
        margin-top: 4px;
    }
    
    .no-screen-message {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        color: #e0e0e0;
        text-align: center;
        padding: 40px;
    }
    
    .status-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.8;
    }
    
    .no-screen-message h3 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
    }
    
    .no-screen-message p {
        margin: 0;
        font-size: 14px;
        opacity: 0.7;
    }
    
    .viewer-footer {
        display: flex;
        gap: 16px;
        align-items: center;
        padding: 8px 16px;
        background: rgba(40, 40, 40, 0.9);
        border-radius: 0 0 12px 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 11px;
        color: #b0b0b0;
    }
    
    .stats {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .automation-status {
        color: #4ade80;
        font-weight: 600;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.2);
            opacity: 0.7;
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
        .screen-viewer-container {
            background: rgba(10, 10, 10, 0.95);
        }
        
        .viewer-header {
            background: rgba(20, 20, 20, 0.9);
        }
        
        .viewer-footer {
            background: rgba(20, 20, 20, 0.9);
        }
    }
</style>