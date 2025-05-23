<script>
    import { onMount } from 'svelte';
    import EyeWidget from './components/EyeWidget.svelte';
    import NextGenAppleChatWidget from './components/NextGenAppleChatWidget.svelte';
    
    let showChat = false;
    let isInitialized = false;
    
    onMount(() => {
        console.log('Initializing Next-Gen SensAI Overlay');
        
        // Add keyboard shortcut for global toggle
        document.addEventListener('keydown', handleGlobalKeyDown);
        
        // Initialize with slight delay for smooth startup
        setTimeout(() => {
            isInitialized = true;
        }, 100);
        
        return () => {
            document.removeEventListener('keydown', handleGlobalKeyDown);
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
        }
    }
    
    // Handle chat visibility toggle with enhanced feedback
    function handleChatToggle() {
        showChat = !showChat;
        console.log('Next-Gen chat visibility toggled:', showChat);
        
        // Haptic feedback for supported devices
        if (navigator.vibrate) {
            navigator.vibrate(showChat ? [10, 5, 10] : [5]);
        }
        
        // Visual feedback through document class
        if (showChat) {
            document.body.classList.add('chat-open');
        } else {
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
    /* Global overlay styles with next-gen enhancements */
    :global(html, body) {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, system-ui, sans-serif;
        background: transparent !important;
        user-select: none;
        -webkit-user-select: none;
        -webkit-touch-callout: none;
        -webkit-tap-highlight-color: transparent;
    }
    
    /* Enhanced typography for better readability */
    :global(body) {
        font-feature-settings: 'kern' 1, 'liga' 1, 'calt' 1;
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Chat open state styling */
    :global(body.chat-open) {
        backdrop-filter: blur(1px);
        transition: backdrop-filter 0.3s ease;
    }
    
    .next-gen-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 9999;
    }
    
    .next-gen-overlay.initialized {
        opacity: 1;
    }
    
    /* Child components will set pointer-events: auto for interactivity */
    .next-gen-overlay :global(*) {
        box-sizing: border-box;
    }
    
    /* Shortcut hint styling */
    .shortcut-hint {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        pointer-events: none;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .shortcut-hint.visible {
        opacity: 0.7;
        transform: translateY(0);
        animation: hintPulse 3s ease-in-out 2s;
    }
    
    @keyframes hintPulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    /* Accessibility improvements */
    @media (prefers-reduced-motion: reduce) {
        .next-gen-overlay,
        .shortcut-hint {
            transition: none;
            animation: none;
        }
        
        :global(body.chat-open) {
            transition: none;
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .shortcut-hint {
            background: #000;
            border: 1px solid #fff;
        }
    }
    
    /* Dark mode adaptations */
    @media (prefers-color-scheme: dark) {
        .shortcut-hint {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    }
    
    /* Focus management for accessibility */
    :global(:focus-visible) {
        outline: 2px solid #007AFF;
        outline-offset: 2px;
    }
    
    /* Custom scrollbar styling for webkit browsers */
    :global(::-webkit-scrollbar) {
        width: 8px;
        height: 8px;
    }
    
    :global(::-webkit-scrollbar-track) {
        background: transparent;
    }
    
    :global(::-webkit-scrollbar-thumb) {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
    }
    
    :global(::-webkit-scrollbar-thumb:hover) {
        background: rgba(0, 0, 0, 0.3);
    }
    
    @media (prefers-color-scheme: dark) {
        :global(::-webkit-scrollbar-thumb) {
            background: rgba(255, 255, 255, 0.2);
        }
        
        :global(::-webkit-scrollbar-thumb:hover) {
            background: rgba(255, 255, 255, 0.3);
        }
    }
    
    /* Performance optimizations */
    .next-gen-overlay {
        will-change: opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
    }
    
    /* Mobile viewport handling */
    @media screen and (max-width: 768px) {
        .shortcut-hint {
            display: none; /* Hide on mobile as touch interaction is primary */
        }
    }
    
    /* Print styles */
    @media print {
        .next-gen-overlay {
            display: none;
        }
    }
</style>