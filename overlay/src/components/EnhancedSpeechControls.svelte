<script>
    import { onMount, onDestroy } from 'svelte';
    import { speechService, speak, cancelSpeech, toggleSpeech } from '../services/speech.js';
    import { sound, haptic } from '../services/enhanced_interactions.js';
    
    // Props
    export let messages = [];
    export let currentMode = 'Ask'; // Current mode from parent component
    export let modeColors = {}; // Mode colors from parent component
    
    // State
    let previousMessageCount = 0;
    let speaking = false;
    let enabled = speechService.enabled;
    let mounted = false;
    let showControls = false;
    let autoRead = true;
    let activeColor = '#007AFF';
    
    // Update active color based on current mode
    $: if (currentMode && modeColors && modeColors[currentMode]) {
        activeColor = modeColors[currentMode].color || modeColors[currentMode];
    }
    
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
    $: if (mounted && messages.length > previousMessageCount && enabled && autoRead) {
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
            
            // Provide feedback
            haptic('light');
            sound(enabled ? 'interface-toggle' : 'interface-click');
            
            if (enabled) {
                // Read latest assistant message as confirmation
                const assistantMessages = messages.filter(m => m.role === 'assistant');
                if (assistantMessages.length > 0) {
                    const latestMessage = assistantMessages[assistantMessages.length - 1];
                    speak("Text to speech enabled. Latest response: " + latestMessage.content);
                } else {
                    speak("Text to speech enabled");
                }
            }
        }
    }
    
    function toggleAutoRead() {
        autoRead = !autoRead;
        haptic('light');
        sound('interface-toggle');
    }
    
    function toggleControls() {
        showControls = !showControls;
        haptic('light');
        sound('interface-click');
    }
    
    function readMessage(idx) {
        if (!enabled) return;
        
        const message = messages[idx];
        if (message && message.content) {
            speak(message.content);
            haptic('light');
        }
    }
    
    // Speed controls
    function adjustSpeed(change) {
        const newRate = Math.max(0.5, Math.min(2.0, speechService.rate + change));
        speechService.setRate(newRate);
        haptic('light');
        sound('interface-click');
        
        // If speaking, restart with new rate
        if (speaking) {
            const currentUtterance = speechService.pendingUtterance;
            if (currentUtterance) {
                const text = currentUtterance.text;
                cancelSpeech();
                speak(text);
            }
        }
    }
</script>

<div class="speech-controls-container" style="--active-color: {activeColor}">
    <!-- Button for integrated UI - simplified style -->
    <button 
        class="main-speech-button compact" 
        class:enabled={enabled}
        class:speaking={speaking}
        on:click={handleToggle}
        title={enabled ? (speaking ? "Stop speaking" : "Text-to-speech enabled") : "Enable text-to-speech"}
        aria-label={enabled ? (speaking ? "Stop speaking" : "Text-to-speech enabled") : "Enable text-to-speech"}
        aria-pressed={enabled}
    >
        {#if speaking}
            <!-- Speaking icon - wave form -->
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19 8C20.66 9.65 20.66 14.35 19 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15 11C15.6 11.45 15.6 12.55 15 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else if enabled}
            <!-- Enabled icon -->
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19.07 4.93C20.9447 6.80528 21.9979 9.34836 22 12C22 14.6522 20.9447 17.1957 19.07 19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15.54 8.46C16.4774 9.39764 17.004 10.6692 17.004 11.995C17.004 13.3208 16.4774 14.5924 15.54 15.53" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else}
            <!-- Disabled icon -->
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 9.5L20.5 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 16L20.5 9.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {/if}
    </button>
    
    <!-- Extended Controls Panel -->
    {#if showControls}
        <div class="speech-panel" in:slide={{duration: 200, delay: 50}} out:slide={{duration: 150}}>
            <div class="speech-panel-header">
                <span>Voice Controls</span>
                <button class="close-button" on:click={toggleControls}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            
            <div class="speech-panel-body">
                <!-- Master Toggle -->
                <div class="control-row">
                    <span>Text-to-Speech</span>
                    <button class="toggle-button" class:active={enabled} on:click={handleToggle}>
                        <div class="toggle-track">
                            <div class="toggle-indicator"></div>
                        </div>
                    </button>
                </div>
                
                <!-- Auto-read Toggle -->
                <div class="control-row">
                    <span>Auto-read responses</span>
                    <button class="toggle-button" class:active={autoRead} on:click={toggleAutoRead}>
                        <div class="toggle-track">
                            <div class="toggle-indicator"></div>
                        </div>
                    </button>
                </div>
                
                <!-- Speed Controls -->
                <div class="control-row">
                    <span>Speed</span>
                    <div class="speed-controls">
                        <button class="speed-button" on:click={() => adjustSpeed(-0.1)} disabled={speechService.rate <= 0.5}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                        <span class="speed-value">{speechService.rate.toFixed(1)}x</span>
                        <button class="speed-button" on:click={() => adjustSpeed(0.1)} disabled={speechService.rate >= 2.0}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 5V19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="action-buttons">
                    {#if speaking}
                        <button class="action-button stop" on:click={() => cancelSpeech()}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="6" y="6" width="12" height="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Stop
                        </button>
                    {:else}
                        <button class="action-button play" on:click={() => {
                            const assistantMessages = messages.filter(m => m.role === 'assistant');
                            if (assistantMessages.length > 0) {
                                const latestMessage = assistantMessages[assistantMessages.length - 1];
                                speak(latestMessage.content);
                            }
                        }} disabled={!enabled || messages.filter(m => m.role === 'assistant').length === 0}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M5 3L19 12L5 21V3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Play Latest
                        </button>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
    
    <!-- Message-specific read buttons -->
    {#if enabled && !showControls}
        <div class="read-buttons-container">
            {#each messages as message, i}
                {#if message.role === 'assistant'}
                    <button 
                        class="read-message-button"
                        style="top: {message.offsetTop || 0}px"
                        class:active={speaking && speechService.pendingUtterance && speechService.pendingUtterance.text.includes(message.content.substring(0, 20))}
                        on:click={() => readMessage(i)}
                        title="Read this message"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            {#if speaking && speechService.pendingUtterance && speechService.pendingUtterance.text.includes(message.content.substring(0, 20))}
                                <!-- Stop icon -->
                                <rect x="6" y="6" width="12" height="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            {:else}
                                <!-- Play icon -->
                                <path d="M5 3L19 12L5 21V3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            {/if}
                        </svg>
                    </button>
                {/if}
            {/each}
        </div>
    {/if}
</div>

<style>
    .speech-controls-container {
        position: relative;
        z-index: 100;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .main-speech-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: transparent;
        border: none;
        cursor: pointer;
        border-radius: 50%;
        transition: all 0.2s ease;
        opacity: 0.8;
        color: #888;
        padding: 0;
    }
    
    .main-speech-button.compact {
        width: 28px;
        height: 28px;
        border-radius: 14px;
    }
    
    .main-speech-button:hover {
        opacity: 1;
        background-color: rgba(255, 255, 255, 0.1);
        transform: scale(1.05);
    }
    
    .main-speech-button.enabled {
        opacity: 0.9;
        background-color: rgba(255, 255, 255, 0.25);
        color: var(--active-color);
    }
    
    .main-speech-button.speaking {
        opacity: 1;
        animation: pulse 2s infinite;
        background-color: rgba(255, 255, 255, 0.3);
        color: var(--active-color);
    }
    
    .main-speech-button.expanded {
        background-color: var(--active-color);
        color: white;
        opacity: 1;
    }
    
    .speech-panel {
        position: absolute;
        top: 40px;
        right: -30px;
        width: 250px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        box-shadow: 0 5px 25px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(10px);
        overflow: hidden;
        z-index: 101;
    }
    
    .speech-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        font-weight: 500;
        font-size: 14px;
    }
    
    .close-button {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 2px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #888;
    }
    
    .close-button:hover {
        background: rgba(0, 0, 0, 0.05);
        color: #333;
    }
    
    .speech-panel-body {
        padding: 12px 16px;
    }
    
    .control-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
    }
    
    .toggle-button {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0;
        display: flex;
        align-items: center;
    }
    
    .toggle-track {
        width: 40px;
        height: 20px;
        background-color: #D1D1D6;
        border-radius: 10px;
        position: relative;
        transition: background-color 0.2s;
    }
    
    .toggle-indicator {
        width: 16px;
        height: 16px;
        background-color: white;
        border-radius: 50%;
        position: absolute;
        top: 2px;
        left: 2px;
        transition: transform 0.2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }
    
    .toggle-button.active .toggle-track {
        background-color: var(--active-color);
    }
    
    .toggle-button.active .toggle-indicator {
        transform: translateX(20px);
    }
    
    .speed-controls {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .speed-button {
        width: 24px;
        height: 24px;
        background: rgba(0, 0, 0, 0.05);
        border: none;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #555;
    }
    
    .speed-button:hover:not(:disabled) {
        background: rgba(0, 0, 0, 0.1);
        color: #333;
    }
    
    .speed-button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    
    .speed-value {
        width: 36px;
        text-align: center;
        font-variant-numeric: tabular-nums;
    }
    
    .action-buttons {
        display: flex;
        gap: 8px;
        margin-top: 16px;
    }
    
    .action-button {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 12px;
        border-radius: 8px;
        border: none;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .action-button.play {
        background-color: var(--active-color);
        color: white;
    }
    
    .action-button.play:hover:not(:disabled) {
        background-color: color-mix(in srgb, var(--active-color) 85%, black);
    }
    
    .action-button.stop {
        background-color: #FF3B30;
        color: white;
    }
    
    .action-button.stop:hover {
        background-color: #E0352B;
    }
    
    .action-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .read-buttons-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 90;
    }
    
    .read-message-button {
        position: absolute;
        right: 65px;
        width: 28px;
        height: 28px;
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--active-color);
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        opacity: 0.7;
    }
    
    .read-message-button:hover {
        opacity: 1;
        transform: scale(1.05);
        background: rgba(255, 255, 255, 0.9);
    }
    
    .read-message-button.active {
        background: var(--active-color);
        color: white;
        opacity: 1;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 0.8;
        }
        50% {
            transform: scale(1.05);
            opacity: 1;
        }
        100% {
            transform: scale(1);
            opacity: 0.8;
        }
    }
    
    /* Animation for panel */
    @keyframes slide-in {
        from {
            transform: translateY(-10px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slide-out {
        from {
            transform: translateY(0);
            opacity: 1;
        }
        to {
            transform: translateY(-10px);
            opacity: 0;
        }
    }
    
    .slide-in {
        animation: slide-in 0.2s ease forwards;
    }
    
    .slide-out {
        animation: slide-out 0.15s ease forwards;
    }
</style>