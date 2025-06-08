<script>
    import { onMount, onDestroy } from 'svelte';
    import { speechService, speak, cancelSpeech, toggleSpeech } from '../services/speech.js';
    
    // Props
    export let messages = [];
    export let position = 'topright'; // topright, topleft, bottomright, bottomleft
    export let size = '24px';
    export let activeColor = '#007AFF';
    
    // State
    let previousMessageCount = 0;
    let speaking = false;
    let enabled = speechService.enabled;
    let mounted = false;
    
    // Setup event listeners and check initial state
    onMount(() => {
        mounted = true;
        previousMessageCount = messages.length;
        
        // Listen for speech events
        window.addEventListener('speech-started', handleSpeechStarted);
        window.addEventListener('speech-ended', handleSpeechEnded);
        window.addEventListener('speech-error', handleSpeechEnded);
        
        return () => {
            window.removeEventListener('speech-started', handleSpeechStarted);
            window.removeEventListener('speech-ended', handleSpeechEnded);
            window.removeEventListener('speech-error', handleSpeechEnded);
            
            // Cancel any ongoing speech
            if (speaking) {
                cancelSpeech();
            }
        };
    });
    
    // Watch for new messages to read them automatically
    $: if (mounted && messages.length > previousMessageCount && enabled) {
        const latestMessage = messages[messages.length - 1];
        if (latestMessage && latestMessage.role === 'assistant') {
            speak(latestMessage.content);
        }
        previousMessageCount = messages.length;
    }
    
    function handleSpeechStarted() {
        speaking = true;
    }
    
    function handleSpeechEnded() {
        speaking = false;
    }
    
    function handleToggle() {
        if (speaking) {
            cancelSpeech();
            speaking = false;
        } else {
            enabled = toggleSpeech();
        }
    }
    
    // Calculate position classes
    $: positionClass = {
        'topright': 'top-right',
        'topleft': 'top-left',
        'bottomright': 'bottom-right',
        'bottomleft': 'bottom-left'
    }[position] || 'top-right';
</script>

<div class="speech-controls {positionClass}">
    <button 
        class="speech-toggle" 
        class:enabled={enabled}
        class:speaking={speaking}
        on:click={handleToggle}
        title={enabled ? (speaking ? "Stop speaking" : "Text-to-speech enabled") : "Text-to-speech disabled"}
        aria-label={enabled ? (speaking ? "Stop speaking" : "Text-to-speech enabled") : "Text-to-speech disabled"}
        aria-pressed={enabled}
    >
        {#if speaking}
            <!-- Speaking icon - wave form -->
            <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 8V16" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 6V18" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15 10V14" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18 8V16" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 10V14" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else if enabled}
            <!-- Enabled icon -->
            <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15.54 8.46C16.4774 9.39764 17.004 10.6692 17.004 11.995C17.004 13.3208 16.4774 14.5924 15.54 15.53" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19 5C20.2731 6.52779 21 8.51843 21 10.6667C21 12.8149 20.2731 14.8056 19 16.3333" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else}
            <!-- Disabled icon -->
            <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M23 9L17 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 9L23 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {/if}
    </button>
</div>

<style>
    .speech-controls {
        position: absolute;
        z-index: 100;
    }
    
    .top-right {
        top: 10px;
        right: 50px;
    }
    
    .top-left {
        top: 10px;
        left: 50px;
    }
    
    .bottom-right {
        bottom: 10px;
        right: 50px;
    }
    
    .bottom-left {
        bottom: 10px;
        left: 50px;
    }
    
    .speech-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.15);
        border: none;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        transition: all 0.2s ease;
        opacity: 0.7;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
    }
    
    .speech-toggle:hover {
        opacity: 1;
        background-color: rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
    }
    
    .speech-toggle.enabled {
        opacity: 0.9;
        background-color: rgba(255, 255, 255, 0.25);
    }
    
    .speech-toggle.speaking {
        opacity: 1;
        animation: pulse 2s infinite;
        background-color: rgba(255, 255, 255, 0.3);
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
</style>