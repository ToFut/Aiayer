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