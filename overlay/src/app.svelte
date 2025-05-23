<script>
    import { onMount } from 'svelte';
    import EyeWidget from './components/EyeWidget.svelte';
    import NextGenAppleChatWidget from './components/NextGenAppleChatWidget.svelte';
    import { enhancedInteractions, haptic, sound } from './services/enhanced_interactions.js';
    
    let showChat = false;
    let isInitialized = false;
    
    onMount(() => {
        console.log('Initializing Next-Gen SensAI Overlay');
        
        // Initialize enhanced interactions
        enhancedInteractions.loadSettings();
        
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
    
    <!-- Next-Generation Apple-inspired Chat Widget -->
    <NextGenAppleChatWidget 
        show={showChat} 
        initialPosition={getInitialPosition()}
        wsEndpoint="ws://localhost:8765"
        on:positionchange={handlePositionChange}
        on:close={() => showChat = false}
    />
    
    <!-- Global keyboard shortcut hint -->
    {#if isInitialized && !showChat}
        <div class="shortcut-hint" class:visible={!showChat}>
            <span>⌘⇧A to open chat</span>
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
</style>