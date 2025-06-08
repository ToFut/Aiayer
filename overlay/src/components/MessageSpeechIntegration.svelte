<script>
    import { onMount, onDestroy } from 'svelte';
    import { speak, cancelSpeech, toggleSpeech, speechService } from '../services/speech.js';
    import SpeechToggle from './SpeechToggle.svelte';
    
    // Prop to observe the messages array
    export let messages = [];
    // Automatically read new messages
    export let autoRead = true;
    
    let previousMessageCount = 0;
    let speechEnabled = speechService.enabled;
    
    onMount(() => {
        previousMessageCount = messages.length;
        
        return () => {
            // Clean up speech when component is destroyed
            cancelSpeech();
        };
    });
    
    // Watch for new messages to read them
    $: if (messages.length > previousMessageCount && autoRead && speechEnabled) {
        const latestMessage = messages[messages.length - 1];
        if (latestMessage && latestMessage.role === 'assistant') {
            speak(latestMessage.content);
        }
        previousMessageCount = messages.length;
    }
    
    // Toggle speech and remember state
    function handleToggle() {
        speechEnabled = toggleSpeech();
    }
    
    // Read a specific message
    export function readMessage(messageContent) {
        if (speechEnabled) {
            speak(messageContent);
        }
    }
</script>

<div class="speech-integration">
    <SpeechToggle size="24px" />
</div>

<style>
    .speech-integration {
        position: absolute;
        top: 12px;
        right: 50px;
        z-index: 100;
    }
</style>