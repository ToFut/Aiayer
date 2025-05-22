<script>
    import { onMount } from 'svelte';
    import EyeWidget from './components/EyeWidget.svelte';
    import EnterpriseChatWidget from './components/EnterpriseChatWidget.svelte';
    
    let showChat = false;
    
    onMount(() => {
        console.log('Initializing Enterprise SensAI Overlay');
    });
    
    // Handle chat visibility toggle
    function handleChatToggle() {
        showChat = !showChat;
        console.log('Enterprise chat visibility toggled:', showChat);
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
    
    <EnterpriseChatWidget 
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