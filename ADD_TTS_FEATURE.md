# Adding Text-to-Speech to SensAI Overlay

This guide explains how to add text-to-speech capabilities to the SensAI overlay system, allowing AI responses to be read aloud automatically.

## Features

- Toggle text-to-speech on/off with a simple button
- Automatic reading of new AI responses 
- Smart voice selection using system preferred voices
- Settings persistence between sessions
- Clean processing of response text (removes code blocks, markdown formatting, etc.)

## Installation Steps

1. **Add the Speech Service**

First, create the speech service file:

```bash
# Navigate to services directory
cd overlay/src/services

# Create the speech service file
touch speech.js
```

Copy the following code into `speech.js`:

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

2. **Create the Speech Controls Component**

Create a new file for the speech controls UI component:

```bash
# Navigate to components directory
cd overlay/src/components

# Create the speech controls component file
touch SpeechControls.svelte
```

Copy the following code into `SpeechControls.svelte`:

```svelte
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
```

3. **Modify NextGenAppleChatWidget.svelte**

Now, integrate the speech controls into your main chat widget component:

```bash
# Edit the NextGenAppleChatWidget.svelte file
code overlay/src/components/NextGenAppleChatWidget.svelte
```

Add the following import at the top of the script section:

```svelte
import SpeechControls from './SpeechControls.svelte';
```

Find a suitable location in the component's template to add the SpeechControls component. For example, right after the main container opens:

```svelte
<div class="chat-widget-container" class:show={show} style="left: {position.x}px; top: {position.y}px;" bind:this={chatContainer} on:mousedown={handleDragStart}>
  <!-- Add speech controls here -->
  <SpeechControls messages={messages} position="topright" activeColor={modes[currentMode].color} />
  
  <!-- Rest of your chat widget HTML -->
</div>
```

## Usage

The speech controls should now be visible in your chat interface. Here's how to use them:

1. Click the speaker icon to toggle text-to-speech on/off
2. When enabled, all new AI responses will be automatically read aloud
3. Click the icon while speech is in progress to stop it
4. Settings (enabled/disabled state) will be remembered between sessions

## Customization

You can customize the speech service by modifying the following settings:

- **Voice**: The service will automatically select the best available voice in your system language
- **Position**: Change the 'position' prop to "topleft", "topright", "bottomleft", or "bottomright"
- **Colors**: Change the 'activeColor' prop to match your theme
- **Size**: Adjust the 'size' prop to make the icon larger or smaller

## Troubleshooting

- If you don't hear any speech, check that your system has text-to-speech voices installed
- Some browsers may require user interaction before allowing speech synthesis
- For better performance, consider reducing the content length by using the 'cleanTextForSpeech' function

For advanced customization, you can modify the speech.js file to adjust rate, pitch, and voice selection logic.