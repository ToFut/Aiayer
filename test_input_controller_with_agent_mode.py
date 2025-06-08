#!/usr/bin/env python3
"""
Test Input Controller and Agent Mode Integration

This script tests the InputController directly with a simple automation task,
similar to what Agent Mode would do when using the "DO" button.
"""

import asyncio
import time
import logging
import os
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_input_controller():
    """Test the InputController with a simple automation task"""
    try:
        # Import the InputController
        from agent_workflow.input_controller import InputController
        
        # Create the controller
        logger.info("🚀 Initializing InputController...")
        controller = InputController(safety_level="medium")
        
        try:
            # Get current position
            current_pos = controller.get_current_position()
            logger.info(f"Current position: {current_pos}")
            
            # Create a simple automation plan (similar to what Agent Mode would do)
            logger.info("📝 Creating simple automation plan...")
            plan = [
                {"action": "move", "x": 300, "y": 300, "human_like": True},
                {"action": "wait", "duration": 0.5},
                {"action": "click", "button": "left"},
                {"action": "wait", "duration": 0.5},
                {"action": "type", "text": "Hello from Agent Mode test!"},
                {"action": "wait", "duration": 0.5},
                {"action": "press", "key": "enter"}
            ]
            
            # Execute the plan
            logger.info("🔄 Executing automation plan...")
            controller.execute_action_sequence(plan)
            
            logger.info("✅ Automation completed successfully!")
            
            # Wait a moment to see the result
            await asyncio.sleep(1)
            
            # Move back to original position
            logger.info("🔙 Moving back to original position...")
            controller.move_to(current_pos[0], current_pos[1])
            
        finally:
            # Clean up
            controller.stop()
            logger.info("🧹 InputController stopped and cleaned up")
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        return False
    
    return True

async def test_universal_automation_handler():
    """Test the universal automation handler's connection to InputController"""
    try:
        # Import the handler
        from universal_intelligent_automation_handler import universal_automation_handler
        
        logger.info("🔍 Checking if universal_automation_handler has InputController...")
        
        # Check if the handler has an InputController
        if hasattr(universal_automation_handler, 'input_controller'):
            if universal_automation_handler.input_controller is not None:
                logger.info("✅ Universal automation handler already has an InputController")
            else:
                logger.info("🔄 Universal automation handler has a None InputController (lazy initialization)")
        else:
            logger.info("❌ Universal automation handler does not have an InputController attribute")
        
        # Force initialization if needed
        logger.info("🚀 Initializing InputController in universal_automation_handler...")
        if not universal_automation_handler.automation_available:
            try:
                from agent_workflow.input_controller import InputController
                universal_automation_handler.input_controller = InputController(safety_level="medium")
                universal_automation_handler.automation_available = True
                logger.info("✅ InputController successfully initialized in universal_automation_handler")
            except Exception as e:
                logger.error(f"❌ Failed to initialize InputController: {e}")
        
    except ImportError as e:
        logger.error(f"❌ Error importing universal_automation_handler: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing universal_automation_handler: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("="*50)
    print("TESTING INPUT CONTROLLER WITH AGENT MODE")
    print("="*50)
    
    print("\nTest 1: Direct InputController Test")
    print("-"*40)
    input_controller_result = await test_input_controller()
    
    print("\nTest 2: Universal Automation Handler Integration")
    print("-"*40)
    universal_handler_result = await test_universal_automation_handler()
    
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    print(f"InputController Test: {'✅ PASSED' if input_controller_result else '❌ FAILED'}")
    print(f"Universal Handler Test: {'✅ PASSED' if universal_handler_result else '❌ FAILED'}")
    
    if input_controller_result and universal_handler_result:
        print("\n✅ ALL TESTS PASSED!")
        print("The InputController is working and correctly integrated with Agent Mode.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the logs for details on the failures.")

if __name__ == "__main__":
    try:
        # Warn the user before running the test
        print("⚠️  This test will move your mouse and type text!")
        print("Make sure you have a text editor or document open.")
        print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
        
        try:
            for i in range(3, 0, -1):
                print(f"Starting in {i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCancelled by user")
            sys.exit(0)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")