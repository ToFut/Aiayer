# Enhanced Text-to-Speech Integration Guide

This guide provides step-by-step instructions for adding professional text-to-speech capabilities to the SensAI overlay system. The implementation includes clickable read buttons next to each message, organized speech controls panel, and seamless integration with the existing mode system.

## Features

- Main speech button that matches the current mode's color scheme
- Expandable control panel with advanced options
- Individual read buttons next to each AI response message
- Speed controls for adjusting speech rate
- Auto-read toggle for automatic reading of new messages
- Remembers settings between sessions
- Haptic and sound feedback

## Step 1: Create the Speech Service

First, create the speech service file:

```javascript
// File: overlay/src/services/speech.js

/**
 * Speech Synthesis Service
 * Provides text-to-speech capabilities for the overlay system
 */

class SpeechService {
  constructor() {
    this.enabled = true;
    this.voice = null;
    this.rate = 1.0;
    this.pitch = 1.0;
    this.volume = 0.8;
    this.voices = [];
    this.speaking = false;
    this.pendingUtterance = null;
    this.loadSettings();
    this.initVoices();
  }

  initVoices() {
    // Check if SpeechSynthesis is supported
    if (!window.speechSynthesis) {
      console.warn('Speech synthesis is not supported in this browser');
      return;
    }

    // Get available voices
    this.voices = window.speechSynthesis.getVoices();
    
    // If voices are not loaded yet, wait for them
    if (this.voices.length === 0) {
      window.speechSynthesis.addEventListener('voiceschanged', () => {
        this.voices = window.speechSynthesis.getVoices();
        this.selectOptimalVoice();
      });
    } else {
      this.selectOptimalVoice();
    }
  }

  selectOptimalVoice() {
    // Try to find a high-quality voice based on preferences
    // Priority: 1. Saved preference, 2. System language + neural/enhanced voices, 3. Default
    const savedVoiceURI = localStorage.getItem('speechService.voiceURI');
    const systemLang = navigator.language || 'en-US';
    
    if (savedVoiceURI) {
      const savedVoice = this.voices.find(v => v.voiceURI === savedVoiceURI);
      if (savedVoice) {
        this.voice = savedVoice;
        return;
      }
    }

    // Look for premium/neural voices first in system language
    const premiumSystemVoice = this.voices.find(v => 
      v.lang.includes(systemLang.split('-')[0]) && 
      (v.name.includes('Neural') || v.name.includes('Premium') || v.name.includes('Enhanced'))
    );
    
    if (premiumSystemVoice) {
      this.voice = premiumSystemVoice;
      return;
    }

    // Then look for any voice in system language
    const systemVoice = this.voices.find(v => v.lang.includes(systemLang.split('-')[0]));
    if (systemVoice) {
      this.voice = systemVoice;
      return;
    }

    // Fallback to any English voice
    const englishVoice = this.voices.find(v => v.lang.includes('en'));
    if (englishVoice) {
      this.voice = englishVoice;
      return;
    }

    // Last resort - use the first available voice
    if (this.voices.length > 0) {
      this.voice = this.voices[0];
    }
  }

  // Speak text with current settings
  speak(text) {
    if (!this.enabled || !window.speechSynthesis || !text) return;
    
    // Cancel any current speech
    this.cancel();

    // Clean up the text (remove markdown, code blocks, etc.)
    const cleanText = this.cleanTextForSpeech(text);
    
    // Create utterance
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Apply settings
    if (this.voice) utterance.voice = this.voice;
    utterance.rate = this.rate;
    utterance.pitch = this.pitch;
    utterance.volume = this.volume;
    
    // Set event handlers
    utterance.onstart = () => {
      this.speaking = true;
      // Dispatch event for UI updates
      window.dispatchEvent(new CustomEvent('speech-started'));
    };
    
    utterance.onend = () => {
      this.speaking = false;
      this.pendingUtterance = null;
      // Dispatch event for UI updates
      window.dispatchEvent(new CustomEvent('speech-ended'));
    };
    
    utterance.onerror = (error) => {
      console.error('Speech synthesis error:', error);
      this.speaking = false;
      this.pendingUtterance = null;
      // Dispatch event for UI updates
      window.dispatchEvent(new CustomEvent('speech-error', { detail: error }));
    };
    
    // Store reference to current utterance
    this.pendingUtterance = utterance;
    
    // Speak
    window.speechSynthesis.speak(utterance);
  }

  // Clean text for speech synthesis (remove markdown, etc.)
  cleanTextForSpeech(text) {
    if (!text) return '';
    
    return text
      // Remove code blocks
      .replace(/```[\s\S]*?```/g, 'Code block omitted.')
      // Remove inline code
      .replace(/`([^`]+)`/g, '$1')
      // Remove Markdown links but keep the text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Remove Markdown emphasis/bold
      .replace(/(\*\*|__)(.*?)\1/g, '$2')
      .replace(/(\*|_)(.*?)\1/g, '$2')
      // Remove special characters that might cause issues
      .replace(/[#>*_~]/g, ' ')
      // Replace multiple spaces with a single space
      .replace(/\s+/g, ' ')
      .trim();
  }

  // Pause current speech
  pause() {
    if (window.speechSynthesis) {
      window.speechSynthesis.pause();
    }
  }

  // Resume paused speech
  resume() {
    if (window.speechSynthesis) {
      window.speechSynthesis.resume();
    }
  }

  // Cancel current speech
  cancel() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      this.speaking = false;
      this.pendingUtterance = null;
    }
  }

  // Toggle speech service on/off
  toggle() {
    this.enabled = !this.enabled;
    
    if (!this.enabled) {
      this.cancel();
    }
    
    this.saveSettings();
    return this.enabled;
  }

  // Set speech rate (0.1 to 2.0)
  setRate(rate) {
    this.rate = Math.max(0.1, Math.min(2.0, rate));
    this.saveSettings();
    return this.rate;
  }

  // Set speech pitch (0.1 to 2.0)
  setPitch(pitch) {
    this.pitch = Math.max(0.1, Math.min(2.0, pitch));
    this.saveSettings();
    return this.pitch;
  }

  // Set speech volume (0.0 to 1.0)
  setVolume(volume) {
    this.volume = Math.max(0.0, Math.min(1.0, volume));
    this.saveSettings();
    return this.volume;
  }

  // Set voice by URI
  setVoice(voiceURI) {
    const newVoice = this.voices.find(v => v.voiceURI === voiceURI);
    if (newVoice) {
      this.voice = newVoice;
      this.saveSettings();
      return true;
    }
    return false;
  }

  // Get available voices
  getVoices() {
    return this.voices;
  }

  // Load settings from localStorage
  loadSettings() {
    try {
      const enabled = localStorage.getItem('speechService.enabled');
      const rate = localStorage.getItem('speechService.rate');
      const pitch = localStorage.getItem('speechService.pitch');
      const volume = localStorage.getItem('speechService.volume');
      
      if (enabled !== null) this.enabled = JSON.parse(enabled);
      if (rate !== null) this.rate = parseFloat(rate);
      if (pitch !== null) this.pitch = parseFloat(pitch);
      if (volume !== null) this.volume = parseFloat(volume);
    } catch (error) {
      console.warn('Could not load speech settings:', error);
    }
  }

  // Save settings to localStorage
  saveSettings() {
    try {
      localStorage.setItem('speechService.enabled', JSON.stringify(this.enabled));
      localStorage.setItem('speechService.rate', this.rate.toString());
      localStorage.setItem('speechService.pitch', this.pitch.toString());
      localStorage.setItem('speechService.volume', this.volume.toString());
      if (this.voice) {
        localStorage.setItem('speechService.voiceURI', this.voice.voiceURI);
      }
    } catch (error) {
      console.warn('Could not save speech settings:', error);
    }
  }
}

// Export singleton instance
export const speechService = new SpeechService();

// Export convenience functions
export const speak = (text) => speechService.speak(text);
export const pauseSpeech = () => speechService.pause();
export const resumeSpeech = () => speechService.resume();
export const cancelSpeech = () => speechService.cancel();
export const toggleSpeech = () => speechService.toggle();
```

## Step 2: Create the Enhanced Speech Controls Component

Create a new component file:

```svelte
<!-- File: overlay/src/components/EnhancedSpeechControls.svelte -->

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
    <!-- Main Button -->
    <button 
        class="main-speech-button" 
        class:enabled={enabled}
        class:speaking={speaking}
        class:expanded={showControls}
        on:click={toggleControls}
        title={enabled ? (speaking ? "Speech controls" : "Speech controls") : "Speech controls"}
        aria-label={enabled ? (speaking ? "Speech controls" : "Speech controls") : "Speech controls"}
    >
        {#if speaking}
            <!-- Speaking icon - wave form -->
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 8V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 6V18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15 10V14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18 8V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 10V14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else}
            <!-- Speaker icon -->
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15.54 8.46C16.4774 9.39764 17.004 10.6692 17.004 11.995C17.004 13.3208 16.4774 14.5924 15.54 15.53" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19 5C20.2731 6.52779 21 8.51843 21 10.6667C21 12.8149 20.2731 14.8056 19 16.3333" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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
        position: absolute;
        top: 12px;
        right: 12px;
        z-index: 100;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    
    .main-speech-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.15);
        border: none;
        cursor: pointer;
        border-radius: 50%;
        transition: all 0.2s ease;
        opacity: 0.7;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        color: #888;
    }
    
    .main-speech-button:hover {
        opacity: 1;
        background-color: rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
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
        top: 50px;
        right: 0;
        width: 250px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
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
```

## Step 3: Modify the Chat Widget Component

In your NextGenAppleChatWidget.svelte file, make the following changes:

1. Import the enhanced speech controls and the 'slide' transition:

```javascript
// Add this to your imports
import { slide } from 'svelte/transition';
import EnhancedSpeechControls from './EnhancedSpeechControls.svelte';
```

2. Find a suitable location to place the speech controls component in your chat widget. Look for the main chat container div - typically it's the first div after the top-level component. Add the component inside this container.

```svelte
<div class="chat-container" or similar>
  <!-- Add the EnhancedSpeechControls here -->
  <EnhancedSpeechControls 
    messages={messages} 
    currentMode={currentMode} 
    modeColors={modes} 
  />
  
  <!-- Rest of your chat container content -->
</div>
```

3. For the message-specific read buttons to work correctly, you need to update your message rendering code to include position information. In your message rendering loop, add an `offsetTop` property to each message object:

```svelte
<!-- In your message rendering code -->
{#each messages as message, i}
  <div 
    class="message" 
    bind:this={messageElements[i]}
    on:DOMNodeInserted={() => {
      if (messageElements[i]) {
        message.offsetTop = messageElements[i].offsetTop;
      }
    }}
  >
    <!-- Your existing message content rendering -->
  </div>
{/each}
```

4. Add this to your script section to track message elements:

```javascript
let messageElements = [];
```

## Step 4: Update Styles

Make sure your main chat widget styles don't conflict with the speech controls. You may need to adjust the position of the speech controls or other elements to ensure a good layout.

## Usage

After integrating these components, you'll have:

1. A main speech button that matches the color scheme of the current mode
2. Expandable speech controls panel with:
   - Toggle for enabling/disabling speech
   - Toggle for auto-reading new messages
   - Speed controls
   - Play/Stop buttons
3. Individual read buttons next to each AI response message

## Customization Options

You can customize the speech controls by modifying:

- **Position**: Adjust the CSS in EnhancedSpeechControls.svelte to position the button anywhere in your UI
- **Colors**: The component automatically uses the current mode's color scheme, but you can customize it further
- **Features**: Add or remove features like voice selection, pitch control, etc.

## Troubleshooting

- If the message-specific read buttons don't appear in the correct positions, ensure your message elements have proper positioning and that the offsetTop values are being set correctly.
- If the speech doesn't work, check that your browser supports the Web Speech API.
- If the controls don't match your app's style, adjust the CSS variables and styles in the EnhancedSpeechControls component.

## Browser Support

The Web Speech API is supported in most modern browsers, including:

- Chrome (desktop and mobile)
- Edge
- Safari (desktop and mobile)
- Firefox (partial support)

For best results, test on Chrome or Edge which have the most complete implementations.