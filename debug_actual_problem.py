#!/usr/bin/env python3
"""
Debug the actual click accuracy problem
"""

import subprocess
import time
import pyautogui
from universal_screen_detector import UniversalScreenDetector
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_click_accuracy():
    """Debug why clicks are not accurate"""
    
    print("🔍 DEBUGGING CLICK ACCURACY PROBLEM")
    print("=" * 50)
    
    try:
        # Step 1: Make sure Safari is open and focused with Google
        print("1️⃣ Opening Safari and navigating to Google...")
        subprocess.run(['open', '-a', 'Safari'], check=True)
        time.sleep(2)
        
        # Navigate to Google
        pyautogui.hotkey('cmd', 'l')
        time.sleep(0.5)
        pyautogui.typewrite('google.com')
        pyautogui.press('return')
        time.sleep(3)
        
        print("2️⃣ Checking current active application...")
        result = subprocess.run([
            'osascript', '-e', 
            'tell application "System Events" to get name of first application process whose frontmost is true'
        ], capture_output=True, text=True, check=True)
        active_app = result.stdout.strip()
        print(f"   Active application: {active_app}")
        
        print("3️⃣ Taking screenshot to verify Google is visible...")
        screenshot = pyautogui.screenshot()
        screenshot.save("debug_current_screen.png")
        print("   Screenshot saved: debug_current_screen.png")
        
        print("4️⃣ Testing universal detection...")
        detector = UniversalScreenDetector()
        coords = detector.get_coordinates_for_step("Search for 'test'")
        print(f"   Detected coordinates: {coords}")
        
        print("5️⃣ Manual inspection of Google search box...")
        # Let's manually check where the Google search box should be
        # Based on typical Google layout, search box is usually around center
        expected_x = pyautogui.size().width // 2
        expected_y = pyautogui.size().height // 3
        print(f"   Expected Google search box area: ({expected_x}, {expected_y})")
        
        print("6️⃣ Testing click at detected coordinates...")
        print(f"   Clicking at: {coords}")
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.5)
        
        print("7️⃣ Typing test text...")
        pyautogui.typewrite("ACCURACY TEST")
        
        print("\n✅ DEBUG COMPLETE")
        print("📊 Check if 'ACCURACY TEST' appeared in the Google search box")
        print("📸 If not, check debug_current_screen.png to see what's on screen")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_click_accuracy()