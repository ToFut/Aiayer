#!/usr/bin/env python3
"""
Test input permissions and accessibility
"""

import pyautogui
import subprocess
import time
import sys

def test_permissions():
    print("🔍 Testing macOS accessibility permissions...")
    
    # Test 1: Screen size detection
    try:
        width, height = pyautogui.size()
        print(f"✅ Screen size detected: {width}x{height}")
    except Exception as e:
        print(f"❌ Screen size detection failed: {e}")
        return False
    
    # Test 2: Mouse position
    try:
        x, y = pyautogui.position()
        print(f"✅ Mouse position detected: ({x}, {y})")
    except Exception as e:
        print(f"❌ Mouse position detection failed: {e}")
        return False
    
    # Test 3: Basic typing (should show dialog if no permissions)
    print("\n🎯 Testing typing in 3 seconds...")
    print("PLEASE FOCUS ON A TEXT EDITOR OR TERMINAL WINDOW!")
    time.sleep(3)
    
    try:
        pyautogui.typewrite("test123", interval=0.1)
        print("✅ Typing test completed")
    except Exception as e:
        print(f"❌ Typing test failed: {e}")
        return False
    
    # Test 4: Key press
    try:
        pyautogui.press('backspace')
        pyautogui.press('backspace') 
        pyautogui.press('backspace')
        pyautogui.press('backspace')
        pyautogui.press('backspace')
        pyautogui.press('backspace')
        pyautogui.press('backspace')
        print("✅ Key press test completed")
    except Exception as e:
        print(f"❌ Key press test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Input automation should work.")
    return True

def check_accessibility_permissions():
    print("\n🔒 Checking accessibility permissions...")
    
    # Run AppleScript to check accessibility permissions
    script = '''
    tell application "System Events"
        try
            set frontApp to name of first application process whose frontmost is true
            return "✅ Accessibility permissions granted"
        on error
            return "❌ Accessibility permissions denied"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        print(result.stdout.strip())
        return "✅" in result.stdout
    except Exception as e:
        print(f"❌ Could not check permissions: {e}")
        return False

def provide_instructions():
    print("\n📋 To grant accessibility permissions:")
    print("1. Open System Preferences/Settings")
    print("2. Go to Security & Privacy → Privacy → Accessibility")
    print("3. Add Terminal (or Python) to the list")
    print("4. Make sure it's checked/enabled")
    print("5. Restart this script")
    print("\n🔄 You may need to restart Terminal after granting permissions")

if __name__ == "__main__":
    print("🤖 Input Controller Permission Test")
    print("=" * 40)
    
    # Check if we have accessibility permissions
    has_permissions = check_accessibility_permissions()
    
    if not has_permissions:
        provide_instructions()
        sys.exit(1)
    
    # Test actual input functionality
    if test_permissions():
        print("\n🚀 Your system is ready for automation!")
    else:
        print("\n❌ Permission issues detected")
        provide_instructions()