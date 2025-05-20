#!/usr/bin/env python3
"""
Generate advanced futuristic audio files for the chat interface.
"""
import numpy as np
from scipy.io import wavfile
import os

def generate_tone(frequency, duration, sample_rate=44100, modulation_freq=None, modulation_depth=None, noise_level=0):
    """Generate a tone with frequency modulation and noise."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Base tone
    if modulation_freq and modulation_depth:
        # Add frequency modulation for a more electronic feel
        mod = modulation_depth * np.sin(2 * np.pi * modulation_freq * t)
        freq = frequency * (1 + mod)
        tone = np.sin(2 * np.pi * freq * t)
    else:
        tone = np.sin(2 * np.pi * frequency * t)
    
    # Add harmonics for richer sound
    tone += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)  # First harmonic
    tone += 0.25 * np.sin(2 * np.pi * frequency * 3 * t)  # Second harmonic
    
    # Add noise if specified
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, len(t))
        tone = tone * (1 - noise_level) + noise * noise_level
    
    return tone

def apply_adsr(tone, attack=0.01, decay=0.05, sustain=0.7, release=0.1, sample_rate=44100):
    """Apply ADSR envelope to a tone."""
    total_length = len(tone)
    
    # Calculate envelope points
    attack_length = int(attack * sample_rate)
    decay_length = int(decay * sample_rate)
    sustain_length = int((total_length - attack_length - decay_length - int(release * sample_rate)) * sustain)
    release_length = int(release * sample_rate)
    
    # Create envelope
    envelope = np.zeros(total_length)
    
    # Attack
    envelope[:attack_length] = np.linspace(0, 1, attack_length)
    
    # Decay
    decay_start = attack_length
    decay_end = decay_start + decay_length
    envelope[decay_start:decay_end] = np.linspace(1, sustain, decay_length)
    
    # Sustain
    sustain_start = decay_end
    sustain_end = sustain_start + sustain_length
    envelope[sustain_start:sustain_end] = sustain
    
    # Release
    release_start = sustain_end
    envelope[release_start:] = np.linspace(sustain, 0, total_length - release_start)
    
    return tone * envelope

def generate_message_sent():
    """Generate a WhatsApp-like sound for sent messages."""
    # WhatsApp sent sound is a short, subtle 'pop' with a slight upward pitch
    sample_rate = 44100
    duration = 0.15  # shorter, subtle sound
    
    # Create a quick rising tone (WhatsApp-like pop)
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Base frequency rising from 800 to 1200 Hz
    freqs = np.linspace(800, 1200, len(t))
    tone = np.sin(2 * np.pi * freqs * t)
    
    # Add a bit of harmonics for richer sound
    tone += 0.3 * np.sin(2 * np.pi * freqs * 2 * t)
    
    # Apply a quick envelope for the pop effect
    tone = apply_adsr(tone, attack=0.01, decay=0.04, sustain=0.1, release=0.1)
    
    return (tone * 32767).astype(np.int16)

def generate_message_received():
    """Generate a Telegram-like sound for received messages."""
    # Telegram received message has a distinctive short "pop" sound
    sample_rate = 44100
    
    # Primary tone - crisp and clear
    duration = 0.07  # Very short duration
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Use a combination of frequencies for a more pleasant sound
    # Starting with higher frequencies that quickly transition to lower ones
    freq_start = 1800
    freq_end = 1200
    freqs = np.linspace(freq_start, freq_end, len(t))
    
    # Create the main tone with frequency modulation
    tone = 0.7 * np.sin(2 * np.pi * freqs * t)
    
    # Add harmonics for richness
    tone += 0.4 * np.sin(2 * np.pi * freqs * 1.5 * t)  # 1.5x harmonic
    tone += 0.2 * np.sin(2 * np.pi * freqs * 2 * t)    # 2x harmonic
    
    # Add a subtle "click" at the beginning
    click_duration = 0.01
    click_samples = int(sample_rate * click_duration)
    click = np.random.normal(0, 0.1, click_samples) * np.linspace(1, 0, click_samples)
    
    # Create final tone with click at the beginning
    full_tone = np.concatenate([click, tone])
    
    # Apply envelope for clean shape
    full_tone = apply_adsr(full_tone, attack=0.005, decay=0.03, sustain=0.5, release=0.03)
    
    return (full_tone * 32767).astype(np.int16)

def generate_notification():
    """Generate a Telegram-like notification sound."""
    # Telegram notification is a distinctive two-tone melodic sound
    sample_rate = 44100
    
    # First tone - bright and clean
    duration1 = 0.10
    t1 = np.linspace(0, duration1, int(sample_rate * duration1), False)
    freq1 = 1047  # C6
    
    # Add a slight frequency rise for more interest
    freq_mod1 = np.linspace(freq1 * 0.98, freq1, len(t1))
    tone1 = np.sin(2 * np.pi * freq_mod1 * t1)
    
    # Add harmonics for richness
    tone1 += 0.5 * np.sin(2 * np.pi * freq_mod1 * 1.5 * t1)
    tone1 += 0.2 * np.sin(2 * np.pi * freq_mod1 * 2 * t1)
    
    # Apply envelope with quick attack
    tone1 = apply_adsr(tone1, attack=0.008, decay=0.03, sustain=0.7, release=0.06)
    
    # Very short silence between tones
    silence = np.zeros(int(sample_rate * 0.02))
    
    # Second tone - higher with more character
    duration2 = 0.12
    t2 = np.linspace(0, duration2, int(sample_rate * duration2), False)
    freq2 = 1319  # E6
    
    # Add a slight frequency modulation for character
    mod_freq = 15  # 15 Hz modulation
    mod_depth = 0.01
    freq_mod = 1 + mod_depth * np.sin(2 * np.pi * mod_freq * t2)
    tone2 = np.sin(2 * np.pi * freq2 * freq_mod * t2)
    
    # Add harmonics with slightly different modulation for complexity
    tone2 += 0.4 * np.sin(2 * np.pi * freq2 * 1.4 * (1 + 0.8 * mod_depth * np.sin(2 * np.pi * 1.1 * mod_freq * t2)) * t2)
    tone2 += 0.15 * np.sin(2 * np.pi * freq2 * 2 * t2)
    
    # Apply envelope with gentle fade
    tone2 = apply_adsr(tone2, attack=0.01, decay=0.08, sustain=0.6, release=0.08)
    
    # Combine the tones
    tone = np.concatenate([tone1, silence, tone2])
    
    # Apply a subtle overall compression for a more professional sound
    tone = np.tanh(1.2 * tone) / 1.2
    
    return (tone * 32767).astype(np.int16)

def main():
    """Generate all audio files."""
    # Create sounds directory if it doesn't exist
    os.makedirs('overlay/public/sounds', exist_ok=True)
    
    # Generate and save audio files
    wavfile.write('overlay/public/sounds/message-sent.wav', 44100, generate_message_sent())
    wavfile.write('overlay/public/sounds/message-received.wav', 44100, generate_message_received())
    wavfile.write('overlay/public/sounds/notification.wav', 44100, generate_notification())
    
    print("Advanced futuristic audio files generated successfully!")

if __name__ == "__main__":
    main() 