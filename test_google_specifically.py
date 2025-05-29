#!/usr/bin/env python3
"""
Test coordinate accuracy specifically on Google search page
"""

import subprocess
import time
import pyautogui
from universal_screen_detector import UniversalScreenDetector

def test_google_accuracy():
    """Test detection accuracy specifically on Google"""
    
    print("🎯 TESTING GOOGLE SEARCH COORDINATE ACCURACY")
    print("=" * 50)
    
    try:
        # Ensure we're on Google specifically
        print("1️⃣ Opening new Safari tab and navigating to Google...")
        subprocess.run(['open', '-a', 'Safari'], check=True)
        time.sleep(1)
        
        # Open new tab
        pyautogui.hotkey('cmd', 't')
        time.sleep(0.5)
        
        # Navigate specifically to Google
        pyautogui.typewrite('https://www.google.com')
        pyautogui.press('return')
        time.sleep(4)  # Wait for Google to fully load
        
        print("2️⃣ Verifying we're on Google...")
        # Take screenshot to verify
        screenshot = pyautogui.screenshot()
        screenshot.save("google_verification.png")
        
        print("3️⃣ Testing universal detection on Google...")
        detector = UniversalScreenDetector()
        coords = detector.get_coordinates_for_step("Search for 'test query'")
        print(f"   Detected coordinates: {coords}")
        
        print("4️⃣ Testing click accuracy...")
        # Click on detected coordinates
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.5)
        
        # Clear any existing text and type test
        pyautogui.hotkey('cmd', 'a')
        time.sleep(0.2)
        pyautogui.typewrite("COORDINATE TEST SUCCESS")
        
        print("5️⃣ Verification...")
        print("📊 Check if 'COORDINATE TEST SUCCESS' appeared in Google search box")
        print("📸 Check google_verification.png to confirm we're on Google")
        print("📸 Check latest detection image for accuracy visualization")
        
        # Show where we clicked
        print(f"🖱️ Clicked at: {coords}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_accuracy()