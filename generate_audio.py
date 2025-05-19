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
    """Generate a futuristic sound for sent messages."""
    # Create a rich tone with multiple frequencies and noise
    base_tone = generate_tone(880, 0.2, modulation_freq=20, modulation_depth=0.1, noise_level=0.05)  # A5
    overtone = generate_tone(1320, 0.2, modulation_freq=15, modulation_depth=0.05)  # E6
    
    # Mix the tones
    tone = 0.7 * base_tone + 0.3 * overtone
    
    # Apply ADSR envelope
    tone = apply_adsr(tone, attack=0.01, decay=0.05, sustain=0.7, release=0.1)
    
    return (tone * 32767).astype(np.int16)

def generate_message_received():
    """Generate a futuristic sound for received messages."""
    # Create a descending sequence with noise
    t1 = generate_tone(660, 0.15, modulation_freq=15, modulation_depth=0.1, noise_level=0.03)  # E5
    t2 = generate_tone(523.25, 0.15, modulation_freq=10, modulation_depth=0.1)  # C5
    t3 = generate_tone(392, 0.15, modulation_freq=5, modulation_depth=0.05)  # G4
    
    # Add some silence between tones
    silence = np.zeros(int(44100 * 0.02))  # 20ms silence
    
    # Mix and concatenate
    tone = np.concatenate([t1, silence, t2, silence, t3])
    
    # Apply ADSR envelope
    tone = apply_adsr(tone, attack=0.02, decay=0.1, sustain=0.6, release=0.15)
    
    return (tone * 32767).astype(np.int16)

def generate_notification():
    """Generate a complex futuristic notification sound."""
    # Create a sequence of modulated tones with noise
    t1 = generate_tone(880, 0.12, modulation_freq=20, modulation_depth=0.15, noise_level=0.05)  # A5
    t2 = generate_tone(1108.73, 0.12, modulation_freq=15, modulation_depth=0.1)  # C#6
    t3 = generate_tone(1318.51, 0.12, modulation_freq=10, modulation_depth=0.05)  # E6
    t4 = generate_tone(1567.98, 0.12, modulation_freq=5, modulation_depth=0.02)  # G6
    
    # Add some silence between tones
    silence = np.zeros(int(44100 * 0.02))  # 20ms silence
    
    # Mix and concatenate
    tone = np.concatenate([t1, silence, t2, silence, t3, silence, t4])
    
    # Apply ADSR envelope
    tone = apply_adsr(tone, attack=0.01, decay=0.05, sustain=0.8, release=0.1)
    
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