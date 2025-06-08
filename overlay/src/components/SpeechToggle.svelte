<script>
    import { onMount, onDestroy } from 'svelte';
    import { speechService, speak, cancelSpeech } from '../services/speech.js';
    
    export let size = '20px';
    export let color = 'currentColor';
    export let activeColor = '#007AFF';
    
    let enabled = speechService.enabled;
    let speaking = false;
    let mounted = false;
    
    onMount(() => {
        mounted = true;
        
        // Listen for speech events
        window.addEventListener('speech-started', handleSpeechStarted);
        window.addEventListener('speech-ended', handleSpeechEnded);
        window.addEventListener('speech-error', handleSpeechEnded);
        
        return () => {
            window.removeEventListener('speech-started', handleSpeechStarted);
            window.removeEventListener('speech-ended', handleSpeechEnded);
            window.removeEventListener('speech-error', handleSpeechEnded);
        };
    });
    
    function handleSpeechStarted() {
        speaking = true;
    }
    
    function handleSpeechEnded() {
        speaking = false;
    }
    
    function toggleSpeech() {
        if (speaking) {
            cancelSpeech();
            speaking = false;
        } else {
            enabled = speechService.toggle();
        }
    }
</script>

<button 
    class="speech-toggle" 
    class:enabled={enabled}
    class:speaking={speaking}
    on:click={toggleSpeech}
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
            <path d="M12 4V20M8 8V16M16 8V16M4 10V14M20 10V14" stroke={activeColor} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    {:else}
        <!-- Disabled icon -->
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 6V18" stroke={color} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 12L6 12" stroke={color} stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    {/if}
</button>

<style>
    .speech-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
        transition: all 0.2s ease;
        opacity: 0.7;
    }
    
    .speech-toggle:hover {
        opacity: 1;
        background-color: rgba(0, 0, 0, 0.05);
    }
    
    .speech-toggle.enabled {
        opacity: 0.9;
    }
    
    .speech-toggle.speaking {
        opacity: 1;
        animation: pulse 2s infinite;
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