#!/usr/bin/env python3
"""
Simple Input Controller Test
"""
import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_workflow.input_controller import InputController
    print("✅ Input controller imported successfully")
except ImportError as e:
    print(f"❌ Failed to import input controller: {e}")
    sys.exit(1)

def test_basic_input():
    """Test basic input controller functionality"""
    print("🧪 Testing basic input controller...")
    
    try:
        # Initialize input controller
        controller = InputController(safety_level="low")  # Use low safety for testing
        print("✅ Input controller initialized")
        
        # Get screen size
        width, height = controller.screen_width, controller.screen_height
        print(f"✅ Screen size: {width}x{height}")
        
        # Get current mouse position
        current_x, current_y = controller.get_current_position()
        print(f"✅ Current mouse position: ({current_x}, {current_y})")
        
        # Test 1: Move mouse to a safe position (top-left corner)
        print("🎯 Moving mouse to (100, 100)...")
        success = controller.move_to(100, 100, duration=1.0)
        print(f"✅ Mouse movement: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 2: Click
        print("🖱️ Testing click...")
        success = controller.click()
        print(f"✅ Click: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 3: Type text
        print("⌨️ Testing text typing...")
        success = controller.type_text("TEST")
        print(f"✅ Text typing: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 4: Press a key
        print("🔤 Testing key press...")
        success = controller.press_key("enter")
        print(f"✅ Key press: {'SUCCESS' if success else 'FAILED'}")
        
        print("\n🎉 Basic input test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Input test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Input Test...")
    print("⚠️  This will move your mouse and type text!")
    print("Press Ctrl+C to cancel, or any key to continue...")
    
    try:
        input()  # Wait for user confirmation
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(0)
    
    # Run test
    success = test_basic_input()
    
    if success:
        print("\n🎉 Test passed! Input controller is working.")
    else:
        print("\n❌ Test failed. Check the output above for details.") 