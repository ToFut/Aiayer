#!/usr/bin/env python3
"""
Debug script to test screen capture functionality and identify permission issues.
"""

def test_screen_capture():
    """Test basic screen capture to debug the black screen issue"""
    print("🔍 Testing screen capture functionality...")
    
    try:
        # Test PIL ImageGrab
        print("1. Testing PIL ImageGrab...")
        import PIL.ImageGrab
        screenshot = PIL.ImageGrab.grab()
        print(f"   ✅ PIL screenshot: {screenshot.size} pixels")
        
        # Save test image
        test_file = "debug_screenshot_test.png"
        screenshot.save(test_file)
        print(f"   💾 Saved test screenshot: {test_file}")
        
        # Check if image is actually captured (not black)
        import numpy as np
        pixels = np.array(screenshot)
        avg_brightness = np.mean(pixels)
        print(f"   📊 Average pixel brightness: {avg_brightness:.1f}")
        
        if avg_brightness < 5:
            print("   ⚠️  WARNING: Screenshot appears to be black/dark")
            print("   📋 This suggests macOS Screen Recording permission is needed")
            return False
        else:
            print("   ✅ Screenshot appears to contain real screen data")
            return True
            
    except Exception as e:
        print(f"   ❌ PIL ImageGrab failed: {e}")
    
    try:
        # Test macOS CoreGraphics if available
        print("2. Testing macOS CoreGraphics...")
        import Quartz.CoreGraphics as CG
        
        # Get main display
        main_display = CG.CGMainDisplayID()
        width = CG.CGDisplayPixelsWide(main_display)
        height = CG.CGDisplayPixelsHigh(main_display)
        print(f"   📺 Display size: {width}x{height}")
        
        # Try to capture screen
        image = CG.CGDisplayCreateImage(main_display)
        if image:
            print("   ✅ CoreGraphics capture successful")
            return True
        else:
            print("   ❌ CoreGraphics capture failed")
            return False
            
    except Exception as e:
        print(f"   ❌ CoreGraphics failed: {e}")
    
    print("\n❌ All screen capture methods failed!")
    print("\n🔧 SOLUTION for macOS:")
    print("1. Open System Preferences → Security & Privacy → Privacy")
    print("2. Click 'Screen Recording' in the left sidebar")
    print("3. Click the lock icon to make changes")
    print("4. Add Terminal or Python to the allowed apps")
    print("5. Restart this script")
    print("\nAlternatively, run this from an app with screen recording permissions.")
    
    return False

if __name__ == "__main__":
    test_screen_capture()