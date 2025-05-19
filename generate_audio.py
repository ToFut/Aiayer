#!/usr/bin/env python3
"""
Generate simple audio files for the chat interface.
"""
import numpy as np
from scipy.io import wavfile
import os

def generate_tone(frequency, duration, sample_rate=44100):
    """Generate a simple sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    return (tone * 32767).astype(np.int16)

def generate_message_sent():
    """Generate a short, high-pitched tone for sent messages."""
    tone = generate_tone(880, 0.1)  # A5 note, 100ms
    return tone

def generate_message_received():
    """Generate a medium-pitched tone for received messages."""
    tone = generate_tone(660, 0.1)  # E5 note, 100ms
    return tone

def generate_notification():
    """Generate a notification sound (two tones)."""
    tone1 = generate_tone(880, 0.1)  # A5 note, 100ms
    tone2 = generate_tone(1108.73, 0.1)  # C#6 note, 100ms
    silence = np.zeros(int(44100 * 0.05))  # 50ms silence
    return np.concatenate([tone1, silence, tone2])

def main():
    """Generate all audio files."""
    # Create sounds directory if it doesn't exist
    os.makedirs('overlay/public/sounds', exist_ok=True)
    
    # Generate and save audio files
    wavfile.write('overlay/public/sounds/message-sent.wav', 44100, generate_message_sent())
    wavfile.write('overlay/public/sounds/message-received.wav', 44100, generate_message_received())
    wavfile.write('overlay/public/sounds/notification.wav', 44100, generate_notification())
    
    print("Audio files generated successfully!")

if __name__ == "__main__":
    main() 