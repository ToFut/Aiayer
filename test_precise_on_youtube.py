#!/usr/bin/env python3
"""
Test precise detection specifically on YouTube search
"""

import subprocess
import time
import pyautogui
from precise_input_detector import PreciseInputDetector

def test_precise_youtube():
    """Test precise detection on YouTube"""
    
    print("🎯 TESTING PRECISE DETECTION ON YOUTUBE")
    print("=" * 50)
    
    try:
        # Open Safari and go to YouTube
        print("1️⃣ Opening Safari and navigating to YouTube...")
        subprocess.run(['open', '-a', 'Safari'], check=True)
        time.sleep(1)
        
        # New tab
        pyautogui.hotkey('cmd', 't')
        time.sleep(0.5)
        
        # Go to YouTube
        pyautogui.typewrite('youtube.com')
        pyautogui.press('return')
        time.sleep(4)  # Wait for YouTube to load
        
        print("2️⃣ Taking screenshot for manual verification...")
        screenshot = pyautogui.screenshot()
        screenshot.save("youtube_before_detection.png")
        
        print("3️⃣ Running precise detection...")
        detector = PreciseInputDetector()
        coords = detector.detect_precise_input_fields("Search YouTube for videos")
        
        print(f"4️⃣ Detected coordinates: {coords}")
        
        print("5️⃣ Testing the detected coordinates...")
        # Click on detected coordinates
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.5)
        
        # Type test text
        pyautogui.typewrite("PRECISE TEST")
        
        print("6️⃣ Taking screenshot after typing...")
        after_screenshot = pyautogui.screenshot()
        after_screenshot.save("youtube_after_typing.png")
        
        print("\n✅ COMPARISON:")
        print("📸 youtube_before_detection.png - shows YouTube before detection")
        print("📸 Latest precise_detection_*.png - shows where system detected")  
        print("📸 youtube_after_typing.png - shows result after typing")
        print(f"🎯 Detected at: {coords}")
        print("📊 Check if 'PRECISE TEST' appears in the YouTube search box")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_precise_youtube()