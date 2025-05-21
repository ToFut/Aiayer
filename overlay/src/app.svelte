<script>
    import { onMount } from 'svelte';
    import EyeWidget from './components/EyeWidget.svelte';
    import EnhancedNextGenChat from './components/EnhancedNextGenChat.svelte';
    import { EnhancedBridge } from './services/enhanced_bridge';
    
    let showChat = false;
    let bridge;
    
    // Initialize bridge with proper options
    onMount(() => {
        console.log('Initializing advanced overlay app');
        
        // Initialize bridge with better options
        bridge = new EnhancedBridge({
            url: 'ws://localhost:8767',  // Updated to match backend server port
            reconnectAttempts: 10,
            reconnectDelay: 1000,
            debug: true
        });
        
        // Connect to backend
        bridge.connect()
            .then(() => {
                console.log('Successfully connected to backend');
            })
            .catch(error => {
                console.error('Failed to connect on startup:', error);
            });
            
        // Make bridge available globally for debugging
        window.bridge = bridge;
        
        // Clean up on unmount
        return () => {
            if (bridge) bridge.disconnect();
        };
    });
    
    // Handle chat visibility toggle
    function handleChatToggle() {
        showChat = !showChat;
        console.log('Chat visibility toggled:', showChat);
    }
    
    // Calculate initial position based on viewport size
    function getInitialPosition() {
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        return {
            x: viewportWidth - 420,
            y: 90
        };
    }
</script>

<main>
    <!-- Include both components -->
    <EyeWidget on:click={handleChatToggle} />
    
    <EnhancedNextGenChat 
        show={showChat} 
        initialPosition={getInitialPosition()}
        wsEndpoint="ws://localhost:8767"
    />
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