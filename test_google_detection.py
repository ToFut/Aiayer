#!/usr/bin/env python3
"""
Test detection specifically on Google search page
"""

import subprocess
import time
import pyautogui
from universal_screen_detector import UniversalScreenDetector

def test_google_detection():
    """Test detection specifically on Google page"""
    
    print("🔍 TESTING GOOGLE SEARCH DETECTION")
    print("=" * 50)
    
    # Open Safari and navigate to Google
    print("🌐 Opening Safari and navigating to Google...")
    
    try:
        # Open Safari
        subprocess.run(['open', '-a', 'Safari'], check=True)
        time.sleep(2)
        
        # Navigate to Google
        pyautogui.hotkey('cmd', 'l')  # Address bar
        time.sleep(0.5)
        pyautogui.typewrite('google.com')
        pyautogui.press('return')
        time.sleep(3)  # Wait for Google to load
        
        print("✅ Google should be loaded now")
        
        # Now test the detection
        detector = UniversalScreenDetector()
        
        step_description = "Search for 'segev halfon'"
        print(f"\n🎯 Testing step: {step_description}")
        
        coords = detector.get_coordinates_for_step(step_description)
        print(f"📍 Detected coordinates: {coords}")
        
        # Try clicking on the detected coordinates to test
        print(f"🖱️  Testing click at {coords}...")
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.5)
        
        # Type some test text
        print("⌨️  Typing test text...")
        pyautogui.typewrite("test search")
        
        print("\n✅ Test complete - check if the search box was correctly targeted")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_google_detection()