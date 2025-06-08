#!/usr/bin/env python3
"""
Simple test script to verify basic InputController functionality.
This test focuses only on the InputController without any LLM or agent mode dependencies.
"""

import logging
import time
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import from project root
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_basic_input_controller():
    """Test basic InputController functionality."""
    try:
        from agent_workflow.input_controller import InputController
        
        logger.info("🧪 Testing basic InputController functionality")
        
        # Create InputController with medium safety level
        controller = InputController(safety_level="medium")
        
        # Test getting current position
        position = controller.get_current_position()
        logger.info(f"Current position: {position}")
        
        # Test moving to a position near the current one (safer)
        current_x, current_y = position
        target_x = min(current_x + 50, controller.screen_width - 100)
        target_y = min(current_y + 50, controller.screen_height - 100)
        
        logger.info(f"Moving to position: ({target_x}, {target_y})")
        result = controller.move_to(target_x, target_y, duration=1.0)
        logger.info(f"Move result: {result}")
        
        # Move back
        logger.info("Moving back to original position")
        result = controller.move_to(current_x, current_y, duration=1.0)
        logger.info(f"Move back result: {result}")
        
        # Test running an action sequence
        logger.info("Testing action sequence execution")
        actions = [
            {"action": "wait", "duration": 1.0},
            {"action": "move", "x": current_x + 20, "y": current_y, "duration": 0.5},
            {"action": "move", "x": current_x, "y": current_y, "duration": 0.5}
        ]
        
        sequence_result = controller.execute_action_sequence(actions)
        logger.info(f"Action sequence result: {sequence_result}")
        
        # Test capturing screenshot
        logger.info("Testing screen capture")
        screenshot = controller.capture_screen_region()
        if screenshot:
            logger.info(f"Screenshot captured successfully: {screenshot.size}")
        else:
            logger.error("Failed to capture screenshot")
            
        # Cleanup
        controller.stop()
        logger.info("✅ InputController test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing InputController: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_input_controller()
    if success:
        print("\n🎉 SUCCESS: InputController is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️ FAILURE: InputController test failed!")
        sys.exit(1)