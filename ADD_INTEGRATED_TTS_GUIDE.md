# Adding Integrated Text-to-Speech to the NextGen Chat

This guide provides the steps to add an elegant, integrated text-to-speech feature to the NextGenAppleChatWidget, with controls neatly organized alongside the other action buttons.

## Implementation Overview

The implementation consists of:

1. A speech service using the Web Speech API
2. Enhanced Speech Controls component with toggle and settings
3. Integration with the existing action buttons in the chat interface
4. Individual read buttons next to each message

## 1. Create the Speech Service

First, create the speech service file at `overlay/src/services/speech.js`:

```javascript
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

## 2. Create the Enhanced Speech Controls Component

Create the speech controls component at `overlay/src/components/EnhancedSpeechControls.svelte`:

```svelte
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
    <!-- Speech Toggle Button for Action Bar -->
    <button 
        class="action-button speech-button" 
        class:active={enabled}
        class:speaking={speaking}
        aria-label={enabled ? (speaking ? "Stop speaking" : "Text-to-speech enabled") : "Enable text-to-speech"}
        on:click={handleToggle}
        style="--button-color: {activeColor};"
    >
        {#if speaking}
            <!-- Speaking icon - wave form -->
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 8V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 6V18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15 10V14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18 8V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 10V14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else if enabled}
            <!-- Enabled icon -->
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15.54 8.46C16.4774 9.39764 17.004 10.6692 17.004 11.995C17.004 13.3208 16.4774 14.5924 15.54 15.53" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {:else}
            <!-- Disabled icon -->
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M23 9L17 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 9L23 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        {/if}
    </button>
    
    <!-- Message-specific read buttons -->
    {#if enabled && !speaking}
        <div class="read-buttons-container">
            {#each messages as message, i}
                {#if message.role === 'assistant' && message.offsetTop}
                    <button 
                        class="read-message-button"
                        style="top: {message.offsetTop}px"
                        on:click={() => readMessage(i)}
                        title="Read this message"
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M5 3L19 12L5 21V3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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
        z-index: 5;
    }
    
    /* Make speech button match other action buttons */
    .speech-button::before {
        background: linear-gradient(135deg, 
            rgba(var(--active-color), 0.15) 0%, 
            rgba(var(--active-color), 0.15) 100%);
    }
    
    .speech-button:hover {
        border-color: rgba(var(--active-color), 0.2);
    }
    
    .speech-button.active {
        background: rgba(var(--active-color), 0.15);
        border-color: rgba(var(--active-color), 0.3);
        color: var(--active-color);
    }
    
    .speech-button.speaking {
        animation: pulse-speech 1.5s infinite;
    }
    
    @keyframes pulse-speech {
        0% { box-shadow: 0 0 0 0 rgba(var(--active-color), 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(var(--active-color), 0); }
        100% { box-shadow: 0 0 0 0 rgba(var(--active-color), 0); }
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
        right: 15px;
        width: 24px;
        height: 24px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--active-color);
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        opacity: 0.5;
    }
    
    .read-message-button:hover {
        opacity: 1;
        transform: scale(1.1);
        background: rgba(255, 255, 255, 0.2);
    }
</style>
```

## 3. Add CSS Styling for Action Buttons in NextGenAppleChatWidget.svelte

Find the action buttons styles in your NextGenAppleChatWidget.svelte file and update them to create a more elegant grouped appearance:

```css
/* Action buttons container */
.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 4px 8px;
  margin-right: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
}

.action-buttons:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.12);
}
```

## 4. Update NextGenAppleChatWidget.svelte

In your NextGenAppleChatWidget.svelte file, make the following updates:

1. Add the EnhancedSpeechControls import:

```javascript
import { onMount, tick } from 'svelte';
import { fade, fly, scale, blur, slide } from 'svelte/transition';
import { cubicOut, elasticOut, expoOut } from 'svelte/easing';
import ScreenViewer from './ScreenViewer.svelte';
import EpiphanyMode from './EpiphanyMode.svelte';
import EnhancedSpeechControls from './EnhancedSpeechControls.svelte';
```

2. Add a messageElements array to track message positions for speech integration:

```javascript
// Track message elements for speech integration
let messageElements = [];
```

3. Update the message rendering to track message positions:

```svelte
{#each messages as message, i (message.id)}
  <div 
    class="message {message.type}"
    bind:this={messageElements[i]}
    on:DOMNodeInserted={() => {
      if (messageElements[i]) {
        message.offsetTop = messageElements[i].offsetTop;
      }
    }}
    in:fly|local={{ y: 20, duration: 300, delay: 50 }}
  >
    <!-- ... rest of your message rendering ... -->
  </div>
{/each}
```

4. Add the EnhancedSpeechControls to the action buttons area:

```svelte
<div class="action-buttons">
  <!-- Voice recording button -->
  <button 
    class="action-button voice-button" 
    aria-label="Voice recording"
    on:click={toggleVoiceRecording}
    class:active={isRecording}
    style="--button-color: #FF453A;"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 1C10.3431 1 9 2.34315 9 4V12C9 13.6569 10.3431 15 12 15C13.6569 15 15 13.6569 15 12V4C15 2.34315 13.6569 1 12 1Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M19 10V12C19 16.4183 15.4183 20 11 20C6.58172 20 3 16.4183 3 12V10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M12 19V23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M8 23H16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>
  
  <!-- Call button -->
  <button 
    class="action-button call-button" 
    class:active={isCallActive}
    aria-label="Phone call"
    on:click={initiateCall}
    style="--button-color: #30D158;"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 16.92V19.92C22.0011 20.1985 21.9441 20.4741 21.8325 20.7293C21.7209 20.9845 21.5573 21.2136 21.3521 21.4018C21.1468 21.5901 20.9046 21.7335 20.6407 21.8227C20.3769 21.9119 20.0974 21.9451 19.82 21.92C16.7428 21.5856 13.787 20.5341 11.19 18.85C8.77383 17.3146 6.72534 15.2661 5.19 12.85C3.49998 10.2412 2.44824 7.27097 2.12 4.18C2.09501 3.90347 2.12788 3.62476 2.2165 3.36162C2.30513 3.09849 2.44757 2.85669 2.63477 2.65162C2.82196 2.44655 3.04981 2.28271 3.30379 2.17052C3.55778 2.05834 3.83214 2.00026 4.11 2H7.11C7.59531 1.99522 8.06579 2.16708 8.43376 2.48353C8.80173 2.79998 9.04207 3.23945 9.11 3.72C9.23662 4.68007 9.47145 5.62273 9.81 6.53C9.94454 6.88792 9.97366 7.27691 9.8939 7.65088C9.81415 8.02485 9.62886 8.36811 9.36 8.64L8.09 9.91C9.51356 12.4135 11.5865 14.4865 14.09 15.91L15.36 14.64C15.6319 14.3711 15.9752 14.1858 16.3491 14.1061C16.7231 14.0263 17.1121 14.0555 17.47 14.19C18.3773 14.5286 19.3199 14.7634 20.28 14.89C20.7658 14.9585 21.2094 15.2032 21.5265 15.5775C21.8437 15.9518 22.0122 16.4296 22 16.92Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>
  
  <!-- Text-to-speech button -->
  <EnhancedSpeechControls 
    messages={messages} 
    currentMode={currentMode} 
    modeColors={modes} 
  />
</div>
```

## Result

After applying these changes, you'll have a fully integrated text-to-speech system with:

1. A speech button in the action buttons area alongside voice recording and call buttons
2. Individual read buttons next to each AI response message
3. Automatic reading of new AI responses
4. Speech controls that match the current mode's color scheme

The implementation is designed to be elegant and consistent with the existing UI design patterns.

## Troubleshooting

If you encounter any issues:

1. **Button Styling**: Make sure the CSS selectors for action buttons are correctly targeting your elements.
2. **Message Position Tracking**: If message buttons aren't appearing in the correct positions, ensure the offsetTop is being correctly set.
3. **Browser Compatibility**: Test on different browsers as the Web Speech API implementation may vary.
4. **Speaking Detection**: If speaking state isn't detected correctly, ensure the event listeners for speech-started and speech-ended are properly set up.

For browsers that don't support the Web Speech API, consider adding a fallback message or disabling the feature with a notice.