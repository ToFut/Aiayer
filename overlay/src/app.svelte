<script>
    import { onMount } from 'svelte';
    import EyeWidget from './components/EyeWidget.svelte';
    import NextGenAppleChatWidget from './components/NextGenAppleChatWidget.svelte';
    import EpiphanyModeHandler from './components/EpiphanyModeHandler.svelte';
    import SpeechToggle from './components/SpeechToggle.svelte';
    import { enhancedInteractions, haptic, sound } from './services/enhanced_interactions.js';
    import { speechService } from './services/speech.js';
    
    let showChat = false;
    let isInitialized = false;
    let epiphanyEnabled = true;
    
    onMount(() => {
        console.log('Initializing Next-Gen SensAI Overlay with Epiphany Mode');
        
        // Initialize enhanced interactions
        enhancedInteractions.loadSettings();
        
        // Load epiphany mode settings
        try {
            const savedSettings = localStorage.getItem('epiphanyModeSettings');
            if (savedSettings) {
                const { enabled } = JSON.parse(savedSettings);
                epiphanyEnabled = enabled;
            }
        } catch (e) {
            console.warn('Could not load epiphany mode settings:', e);
        }
        
        // Add keyboard shortcut for global toggle
        document.addEventListener('keydown', handleGlobalKeyDown);
        
        // Initialize with slight delay for smooth startup
        setTimeout(() => {
            isInitialized = true;
        }, 100);
        
        return () => {
            document.removeEventListener('keydown', handleGlobalKeyDown);
            enhancedInteractions.destroy();
        };
    });
    
    // Global keyboard shortcuts
    function handleGlobalKeyDown(event) {
        // Cmd/Ctrl + Shift + A to toggle chat
        if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'A') {
            event.preventDefault();
            handleChatToggle();
        }
        
        // Cmd/Ctrl + Shift + E to toggle epiphany mode
        if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'E') {
            event.preventDefault();
            toggleEpiphanyMode();
        }
        
        // Escape to close chat when open
        if (event.key === 'Escape' && showChat) {
            event.preventDefault();
            showChat = false;
            sound('interface-close');
        }
    }
    
    // Handle chat visibility toggle with enhanced feedback
    function handleChatToggle() {
        showChat = !showChat;
        console.log('Next-Gen chat visibility toggled:', showChat);
        
        // Enhanced feedback
        if (showChat) {
            haptic('light');
            sound('interface-open');
            document.body.classList.add('chat-open');
        } else {
            haptic('light');
            sound('interface-close');
            document.body.classList.remove('chat-open');
        }
    }
    
    // Toggle epiphany mode
    function toggleEpiphanyMode() {
        epiphanyEnabled = !epiphanyEnabled;
        console.log('Epiphany mode toggled:', epiphanyEnabled);
        
        // Save settings
        try {
            localStorage.setItem('epiphanyModeSettings', JSON.stringify({ enabled: epiphanyEnabled }));
        } catch (e) {
            console.warn('Could not save epiphany mode settings:', e);
        }
        
        // Provide feedback
        haptic('medium');
        sound(epiphanyEnabled ? 'epiphany-on' : 'epiphany-off');
    }
    
    // Handle suggestion from epiphany mode
    function handleSuggestionReceived(event) {
        console.log('Epiphany suggestion received:', event.detail);
        haptic('light');
    }
    
    // Handle suggestion approval
    function handleSuggestionApproved(event) {
        console.log('Epiphany suggestion approved:', event.detail);
        haptic('medium');
    }
    
    // Calculate optimal position based on screen and usage patterns
    function getInitialPosition() {
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Smart positioning based on screen size
        let x, y;
        
        if (viewportWidth > 1400) {
            // Large screens - position away from corners
            x = viewportWidth - 460;
            y = 100;
        } else if (viewportWidth > 1000) {
            // Medium screens - standard position
            x = viewportWidth - 440;
            y = 80;
        } else {
            // Small screens - center and slightly offset
            x = Math.max(20, (viewportWidth - 420) / 2);
            y = 60;
        }
        
        // Load saved position if available
        try {
            const savedPosition = localStorage.getItem('nextGenChatPosition');
            if (savedPosition) {
                const { x: savedX, y: savedY } = JSON.parse(savedPosition);
                // Validate saved position is still within viewport
                if (savedX >= 0 && savedX + 420 <= viewportWidth && 
                    savedY >= 0 && savedY + 680 <= viewportHeight) {
                    x = savedX;
                    y = savedY;
                }
            }
        } catch (e) {
            console.warn('Could not load saved chat position:', e);
        }
        
        return { x, y };
    }
    
    // Get epiphany position
    function getEpiphanyPosition() {
        // Position in top right by default
        return { x: window.innerWidth - 80, y: 20 };
    }
    
    // Save position when chat is moved
    function handlePositionChange(event) {
        try {
            localStorage.setItem('nextGenChatPosition', JSON.stringify(event.detail));
        } catch (e) {
            console.warn('Could not save chat position:', e);
        }
    }
</script>

<main class="next-gen-overlay" class:initialized={isInitialized}>
    <!-- Enhanced Eye Widget with new interaction model -->
    <EyeWidget 
        on:click={handleChatToggle}
        {showChat}
    />
    
    <!-- Next-Generation Cloud-inspired Chat Widget -->
    <NextGenAppleChatWidget 
        show={showChat} 
        initialPosition={getInitialPosition()}
        wsEndpoint="ws://localhost:8767"
        on:positionchange={handlePositionChange}
        on:close={() => showChat = false}
    />
    
    <!-- Epiphany Mode Handler (always active) -->
    {#if isInitialized}
        <EpiphanyModeHandler 
            enabled={epiphanyEnabled}
            position={getEpiphanyPosition()}
            wsEndpoint="ws://localhost:8765"
            soundEnabled={true}
            on:suggestionReceived={handleSuggestionReceived}
            on:suggestionApproved={handleSuggestionApproved}
        />
    {/if}
    
    <!-- Global keyboard shortcut hint -->
    {#if isInitialized && !showChat}
        <div class="shortcut-hint" class:visible={!showChat}>
            <span>⌘⇧A to open chat</span>
            {#if epiphanyEnabled}
                <span class="epiphany-hint">✨ Epiphany mode active (⌘⇧E to toggle)</span>
            {/if}
        </div>
    {/if}
</main>

<style>
    :global(html, body) {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        background: transparent !important;
    }
    
    main {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        pointer-events: none; /* Allow click-through by default */
    }
    
    /* Child components will set pointer-events: auto for interactivity */
    
    .shortcut-hint {
        position: fixed;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.6);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        opacity: 0;
        transition: opacity 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        pointer-events: auto;
    }
    
    .shortcut-hint.visible {
        opacity: 0.8;
    }
    
    .shortcut-hint:hover {
        opacity: 1;
    }
    
    .epiphany-hint {
        margin-top: 4px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        gap: 4px;
        animation: glow 2s infinite alternate;
    }
    
    @keyframes glow {
        from {
            text-shadow: 0 0 0px rgba(255, 255, 255, 0);
        }
        to {
            text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
        }
    }
</style>