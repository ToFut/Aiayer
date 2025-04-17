<script>
    import { onMount } from 'svelte';
    import AssistantWidget from './components/AssistantWidget.svelte';
    import TransformedInterface from './components/TransformedInterface.svelte';
    import { Bridge } from './services/bridge';
    
    let bridge;
    let transformedInterface;
    let isInteractive = false;
    
    onMount(() => {
        bridge = new Bridge();
        bridge.connect();
        
        // Register message handlers
        bridge.on('transform-interface', handleTransformation);
        bridge.on('toggle-interaction', handleInteractionToggle);
        
        // Make bridge available globally
        window.bridge = bridge;
        
        return () => {
            bridge.off('transform-interface', handleTransformation);
            bridge.off('toggle-interaction', handleInteractionToggle);
        };
    });
    
    function handleTransformation(data) {
        if (transformedInterface) {
            transformedInterface.updateLayout(data.rules, data.interactionMap);
        }
    }
    
    function handleInteractionToggle(shouldInteract) {
        isInteractive = shouldInteract;
        if (transformedInterface) {
            transformedInterface.setInteractive(shouldInteract);
        }
    }
    
    function handleWidgetInteraction(shouldInteract) {
        bridge.send('toggle-interaction', { shouldInteract });
    }
</script>

<main>
    <TransformedInterface bind:this={transformedInterface} />
    <AssistantWidget on:toggleInteraction={handleWidgetInteraction} />
</main>

<style>
    main {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }
</style>
