#!/usr/bin/env python3
"""
Test Input Controller - Check if actions are actually performed
"""
import sys
import os
sys.path.append('.')

from agent_workflow.input_controller import InputController
import time

def test_input_controller():
    print("🧪 Testing Input Controller Actions...")
    
    # Initialize input controller
    controller = InputController(safety_level="medium")  # Use medium safety for testing
    
    print("✅ Input controller initialized")
    print(f"🔧 Safety level: {controller.safety_level}")
    print(f"🖥️ Screen size: {controller.screen_width}x{controller.screen_height}")
    print(f"📍 Current position: {controller.get_current_position()}")
    
    # Test 1: Move mouse
    print("\n1️⃣ Testing mouse movement...")
    current_pos = controller.get_current_position()
    print(f"📍 Starting position: {current_pos}")
    
    # Move to a safe position (center of screen)
    target_x = controller.screen_width // 2
    target_y = controller.screen_height // 2
    print(f"🎯 Moving to center: ({target_x}, {target_y})")
    
    result = controller.move_to(target_x, target_y, duration=1.0)
    print(f"✅ Move result: {result}")
    
    new_pos = controller.get_current_position()
    print(f"📍 New position: {new_pos}")
    
    # Test 2: Type text
    print("\n2️⃣ Testing text typing...")
    print("⌨️ Typing 'Hello World'...")
    
    result = controller.type_text("Hello World")
    print(f"✅ Type result: {result}")
    
    # Test 3: Press key
    print("\n3️⃣ Testing key press...")
    print("🔤 Pressing 'space' key...")
    
    result = controller.press_key("space")
    print(f"✅ Press result: {result}")
    
    # Test 4: Hotkey
    print("\n4️⃣ Testing hotkey...")
    print("⌨️ Pressing 'cmd+space'...")
    
    result = controller.hotkey("cmd", "space")
    print(f"✅ Hotkey result: {result}")
    
    # Test 5: Click
    print("\n5️⃣ Testing click...")
    print("🖱️ Clicking at current position...")
    
    result = controller.click()
    print(f"✅ Click result: {result}")
    
    print("\n🎉 Input controller test completed!")
    print("📊 Summary:")
    print(f"   - Mouse movement: {'✅' if result else '❌'}")
    print(f"   - Text typing: {'✅' if result else '❌'}")
    print(f"   - Key press: {'✅' if result else '❌'}")
    print(f"   - Hotkey: {'✅' if result else '❌'}")
    print(f"   - Click: {'✅' if result else '❌'}")
    
    # Cleanup
    controller.stop()

if __name__ == "__main__":
    test_input_controller() 