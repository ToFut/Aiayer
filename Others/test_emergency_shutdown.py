#!/usr/bin/env python3
"""
Test Emergency Shutdown Feature
Demonstrates the Ctrl+1 emergency shutdown functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_workflow.input_controller import InputController
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_emergency_shutdown():
    """Test the emergency shutdown feature."""
    print("🤖 Emergency Shutdown Test")
    print("=" * 50)
    print()
    print("🚨 IMPORTANT: This test will demonstrate the emergency shutdown.")
    print("   Press Ctrl+1 at any time to stop the automation immediately!")
    print()
    print("⚠️  The agent will start moving the mouse in 5 seconds.")
    print("   This is your chance to test the emergency shutdown.")
    print()
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("\n🚀 Starting automation test...")
    
    # Initialize controller
    controller = InputController(safety_level="medium")
    
    try:
        # Continuous mouse movement until emergency shutdown
        print("🔄 Moving mouse in a pattern...")
        print("   Press Ctrl+1 to activate emergency shutdown!")
        
        for i in range(100):  # Will run for a long time unless stopped
            if not controller.running:
                break
                
            # Move in a square pattern
            positions = [
                (300, 300),
                (500, 300), 
                (500, 500),
                (300, 500)
            ]
            
            current_pos = positions[i % 4]
            print(f"🎯 Moving to position {current_pos} (iteration {i+1}/100)")
            
            success = controller.move_to(current_pos[0], current_pos[1])
            if not success:
                print("❌ Movement failed - likely due to emergency shutdown")
                break
                
            time.sleep(2)  # Wait 2 seconds between movements
        
        print("✅ Test completed normally (no emergency shutdown used)")
        
    except SystemExit:
        print("🚨 Emergency shutdown was activated!")
        
    except KeyboardInterrupt:  
        print("\n🛑 Test interrupted by user (Ctrl+C)")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        # Clean up
        try:
            controller.stop()
        except:
            pass
        print("\n✅ Test cleanup completed")

if __name__ == "__main__":
    test_emergency_shutdown()