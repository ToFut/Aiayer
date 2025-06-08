<script>
    import { onMount, onDestroy } from 'svelte';
    import { speak, cancelSpeech } from '../services/speech.js';
    
    // Content to read
    export let text = '';
    // Auto-read when content changes
    export let autoRead = false;
    // Enable/disable the reader
    export let enabled = true;
    
    // Track current speech state
    let speaking = false;
    let mounted = false;
    let previousText = '';
    
    onMount(() => {
        mounted = true;
        
        // Listen for speech events
        window.addEventListener('speech-started', handleSpeechStarted);
        window.addEventListener('speech-ended', handleSpeechEnded);
        window.addEventListener('speech-error', handleSpeechEnded);
        
        if (autoRead && text && enabled) {
            readContent();
        }
        
        return () => {
            window.removeEventListener('speech-started', handleSpeechStarted);
            window.removeEventListener('speech-ended', handleSpeechEnded);
            window.removeEventListener('speech-error', handleSpeechEnded);
        };
    });
    
    onDestroy(() => {
        if (speaking) {
            cancelSpeech();
        }
    });
    
    // Watch for text changes
    $: if (mounted && autoRead && text && text !== previousText && enabled) {
        previousText = text;
        readContent();
    }
    
    function handleSpeechStarted() {
        speaking = true;
    }
    
    function handleSpeechEnded() {
        speaking = false;
    }
    
    function readContent() {
        if (speaking) {
            cancelSpeech();
        }
        
        if (text && enabled) {
            speak(text);
        }
    }
    
    export function stopReading() {
        if (speaking) {
            cancelSpeech();
        }
    }
    
    // Public method to read text
    export function readText(customText) {
        if (speaking) {
            cancelSpeech();
        }
        
        if (customText && enabled) {
            speak(customText);
        } else if (text && enabled) {
            speak(text);
        }
    }
</script>

<!-- This is a utility component with no UI rendering -->