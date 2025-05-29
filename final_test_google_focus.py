#!/usr/bin/env python3
"""
Final test to verify Google search detection works when Google is focused
"""

import subprocess
import time
import pyautogui
from universal_screen_detector import UniversalScreenDetector

def final_test():
    """Final comprehensive test"""
    
    print("🎯 FINAL COMPREHENSIVE TEST")
    print("=" * 50)
    
    try:
        # Focus on Safari with Google
        print("🌐 Focusing on Safari...")
        subprocess.run(['osascript', '-e', 'tell application "Safari" to activate'], check=True)
        time.sleep(2)
        
        # Clear any popups by clicking on main Google area
        pyautogui.click(998, 400)
        time.sleep(1)
        
        # Now test detection
        detector = UniversalScreenDetector()
        
        print("🔍 Testing detection on Google search page...")
        step_description = "Search for 'Claude AI'"
        coords = detector.get_coordinates_for_step(step_description)
        
        print(f"📍 Detected coordinates: {coords}")
        
        # Test the coordinates
        print(f"🖱️  Testing click at detected coordinates...")
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.5)
        
        # Clear any existing text
        pyautogui.hotkey('cmd', 'a')
        time.sleep(0.2)
        
        # Type test text
        test_text = "Test successful"
        print(f"⌨️  Typing: {test_text}")
        pyautogui.typewrite(test_text)
        
        print("\n✅ FINAL TEST COMPLETE")
        print("📊 Check if the text appeared in the Google search box")
        print("📸 Check the latest verification image for detection accuracy")
        
    except Exception as e:
        print(f"❌ Error during final test: {e}")

if __name__ == "__main__":
    final_test()