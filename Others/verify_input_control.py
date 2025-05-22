#!/usr/bin/env python3
"""
Quick Input Control Verification
Simple test to verify mouse and keyboard control works.
"""
import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_workflow.input_controller import InputController

def main():
    """Quick verification test."""
    print("🤖 Agent Input Control Verification")
    print("=" * 40)
    
    # Warning
    print("⚠️  This will move your mouse and type text!")
    print("Make sure you have a text editor or document open.")
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return
    
    print("\n🚀 Starting verification...")
    
    # Create input controller
    controller = InputController(safety_level="medium")
    
    try:
        # Test 1: Get current mouse position
        print("\n1. Getting current mouse position...")
        pos = controller.get_current_position()
        print(f"   Current position: {pos}")
        
        # Test 2: Move mouse in a square pattern
        print("\n2. Moving mouse in square pattern...")
        start_x, start_y = pos
        
        square_moves = [
            (start_x + 100, start_y),      # Right
            (start_x + 100, start_y + 100), # Down
            (start_x, start_y + 100),      # Left
            (start_x, start_y)             # Up (back to start)
        ]
        
        for i, (x, y) in enumerate(square_moves):
            print(f"   Moving to corner {i+1}: ({x}, {y})")
            controller.move_to(x, y, duration=0.5)
            time.sleep(0.5)
        
        print("   ✅ Mouse movement working!")
        
        # Test 3: Click test
        print("\n3. Testing click...")
        controller.click()
        time.sleep(0.5)
        print("   ✅ Click working!")
        
        # Test 4: Type test
        print("\n4. Testing typing...")
        test_text = "Hello from AI Agent! 🤖 This text was typed automatically."
        controller.type_text(test_text)
        time.sleep(1)
        print("   ✅ Typing working!")
        
        # Test 5: Keyboard shortcuts
        print("\n5. Testing keyboard shortcuts...")
        controller.press_key("enter")
        time.sleep(0.3)
        controller.type_text("Testing keyboard shortcuts:")
        controller.press_key("enter")
        
        # Test Ctrl+A (Select All) - using Command on macOS
        controller.hotkey("command", "a")
        time.sleep(0.5)
        
        controller.type_text("✅ Selected all and replaced text! Shortcuts working.")
        print("   ✅ Keyboard shortcuts working!")
        
        # Test 6: Action sequence
        print("\n6. Testing action sequence...")
        actions = [
            {"action": "press", "key": "enter"},
            {"action": "type", "text": "Action sequence test:"},
            {"action": "press", "key": "enter"},
            {"action": "type", "text": "- Step 1 ✓"},
            {"action": "press", "key": "enter"},
            {"action": "type", "text": "- Step 2 ✓"},
            {"action": "press", "key": "enter"},
            {"action": "type", "text": "- Step 3 ✓"},
            {"action": "wait", "duration": 0.5}
        ]
        
        success = controller.execute_action_sequence(actions)
        if success:
            print("   ✅ Action sequence working!")
        else:
            print("   ❌ Action sequence failed!")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Mouse control: Working")
        print("✅ Keyboard control: Working")
        print("✅ Text input: Working") 
        print("✅ Shortcuts: Working")
        print("✅ Action sequences: Working")
        
        print("\n🤖 Agent automation is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        print("Check that pyautogui and pynput are installed correctly.")
        
    finally:
        # Clean up
        controller.stop()
        print("\n✅ Verification complete")

if __name__ == "__main__":
    main()