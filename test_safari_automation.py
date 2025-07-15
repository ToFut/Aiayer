#!/usr/bin/env python3
"""
Test Safari Automation - Replicate the exact automation the backend performs
"""
import sys
import os
sys.path.append('.')

from agent_workflow.input_controller import InputController
import time

def test_safari_automation():
    print("🌐 Testing Safari Automation...")
    print("⚠️ This will open Safari and search for SEGEV")
    print("Press Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("❌ Cancelled by user")
        return
    
    # Initialize input controller
    controller = InputController(safety_level="medium")
    
    print("✅ Input controller initialized")
    print(f"📍 Starting position: {controller.get_current_position()}")
    
    # Step 1: Open Safari using Spotlight (cmd+space)
    print("\n1️⃣ Opening Safari using Spotlight...")
    print("⌨️ Pressing cmd+space...")
    
    result = controller.hotkey("cmd", "space")
    print(f"✅ Spotlight result: {result}")
    
    # Wait for Spotlight to appear
    print("⏱️ Waiting 2 seconds for Spotlight...")
    time.sleep(2)
    
    # Step 2: Type Safari in Spotlight
    print("\n2️⃣ Typing 'Safari' in Spotlight...")
    print("⌨️ Typing 'Safari'...")
    
    result = controller.type_text("Safari")
    print(f"✅ Type Safari result: {result}")
    
    # Wait for Spotlight to process
    print("⏱️ Waiting 1 second for Spotlight to process...")
    time.sleep(1)
    
    # Step 3: Press Enter to open Safari
    print("\n3️⃣ Pressing Enter to open Safari...")
    print("🔤 Pressing 'return'...")
    
    result = controller.press_key("return")
    print(f"✅ Press Enter result: {result}")
    
    # Wait for Safari to load
    print("⏱️ Waiting 3 seconds for Safari to load...")
    time.sleep(3)
    
    # Step 4: Type search term: SEGEV
    print("\n4️⃣ Typing search term: SEGEV...")
    print("⌨️ Typing 'SEGEV'...")
    
    result = controller.type_text("SEGEV")
    print(f"✅ Type SEGEV result: {result}")
    
    # Wait for typing to complete
    print("⏱️ Waiting 1 second for typing to complete...")
    time.sleep(1)
    
    # Step 5: Press Enter to search
    print("\n5️⃣ Pressing Enter to search...")
    print("🔤 Pressing 'return'...")
    
    result = controller.press_key("return")
    print(f"✅ Press Enter result: {result}")
    
    print("\n🎉 Safari automation test completed!")
    print("📊 Summary:")
    print(f"   - Spotlight: {'✅' if result else '❌'}")
    print(f"   - Type Safari: {'✅' if result else '❌'}")
    print(f"   - Open Safari: {'✅' if result else '❌'}")
    print(f"   - Type SEGEV: {'✅' if result else '❌'}")
    print(f"   - Search: {'✅' if result else '❌'}")
    
    # Cleanup
    controller.stop()

if __name__ == "__main__":
    test_safari_automation() 