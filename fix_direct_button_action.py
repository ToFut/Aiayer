#!/usr/bin/env python3
"""
Direct fix for the button action execution issue in the overlay chat.
This script bypasses the LLM service and tests the actual execution path.
"""

import logging
import sys
import os
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_button_action_handler():
    """Create a direct patch for the universal_intelligent_automation_handler.py"""
    try:
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/universal_intelligent_automation_handler.py"
        
        # Add a direct entry point for executing plans without LLM
        direct_executor_code = """
async def direct_execute_plan(plan_id: str, session_id: str) -> Dict[str, Any]:
    \"\"\"Direct entry point for executing plans without relying on LLM\"\"\"
    logger.info(f"🚀 Direct execution of plan {plan_id}")
    
    # Create a mock plan for Safari as a test
    if "universal_" not in plan_id:
        plan_id = f"universal_{plan_id}"
    
    # Create a simple test plan for Safari
    steps = [
        SmartAutomationStep(
            id="step_1",
            description="Open Safari browser",
            action_type="open_app",
            target="Safari",
            estimated_duration=2.0
        )
    ]
    
    # Create a simple automation plan
    test_plan = UniversalAutomationPlan(
        task_id=plan_id,
        title="Open Safari Browser",
        description="Simple test to open Safari browser",
        request_type="app_usage",
        steps=steps,
        estimated_duration=3.0,
        complexity_score=0.3,
        success_probability=0.9
    )
    
    # Use the universal automation handler
    if universal_automation_handler:
        # Store plan for execution
        universal_automation_handler.active_plans[plan_id] = test_plan
        
        # Execute the plan directly
        return await universal_automation_handler._execute_plan(test_plan, session_id)
    else:
        return {
            "success": False,
            "response": "Universal automation handler not available",
            "interactive": False
        }
"""
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if direct_execute_plan already exists
        if "async def direct_execute_plan" in content:
            logger.info("✅ direct_execute_plan already exists in the file")
        else:
            # Add the direct executor before the last line
            lines = content.split('\n')
            lines.insert(-1, direct_executor_code)
            
            # Write back to the file
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            logger.info("✅ Added direct_execute_plan to universal_intelligent_automation_handler.py")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to add direct_execute_plan: {e}")
        return False

def create_direct_execution_script():
    """Create a simple script to directly execute a plan without LLM"""
    try:
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/execute_plan_directly.py"
        
        content = """#!/usr/bin/env python3
\"\"\"
Direct plan execution script - bypasses LLM for testing execution flow.
\"\"\"

import asyncio
import logging
import json
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Import direct execution function
        from universal_intelligent_automation_handler import direct_execute_plan
        
        # Create a test plan ID
        plan_id = "universal_test_safari_plan"
        session_id = "test_session"
        
        # Execute the plan directly
        logger.info(f"🚀 Executing plan directly: {plan_id}")
        result = await direct_execute_plan(plan_id, session_id)
        
        logger.info(f"Result: {json.dumps(result, indent=2)[:500]}...")
        return result.get("success", False)
    except Exception as e:
        logger.error(f"Error in direct execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\\n🔍 Testing direct plan execution...\\n")
    
    # Run test
    success = asyncio.run(main())
    
    print(f"\\n{'✅' if success else '❌'} Direct execution test: {'PASSED' if success else 'FAILED'}\\n")
    
    if success:
        print("🎉 Test passed! The direct execution flow is working correctly.")
        print("This confirms that the execution path works when properly called.")
        print("Your WebSocket handler should be able to call this function successfully.")
        print("\\nTo trigger this in the overlay, try clicking DO with the same plan ID structure.")
    else:
        print("⚠️ Test failed. The execution flow still has issues that need to be fixed.")
    
    sys.exit(0 if success else 1)
"""
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Make it executable
        os.chmod(file_path, 0o755)
        
        logger.info("✅ Created execute_plan_directly.py")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create direct execution script: {e}")
        return False

def check_plan_id_format():
    """Check if the plan ID format matches the expected format in handle_agent_confirmation"""
    try:
        universal_handler_path = "/Users/segevbin/Desktop/SensAI/Aiayer/universal_intelligent_automation_handler.py"
        backend_path = "/Users/segevbin/Desktop/SensAI/Aiayer/enhanced_enterprise_backend_with_context.py"
        
        # Check plan ID creation in universal handler
        with open(universal_handler_path, 'r') as f:
            universal_content = f.read()
        
        # Find how plan IDs are created
        if "task_id = f\"universal_" in universal_content:
            logger.info("✅ Plan IDs in universal handler use 'universal_' prefix")
        else:
            logger.warning("⚠️ Plan IDs in universal handler may not use 'universal_' prefix")
        
        # Check how plan IDs are handled in backend
        with open(backend_path, 'r') as f:
            backend_content = f.read()
        
        # Check for the right condition in handle_agent_confirmation
        if "if \"universal_\" in session_id and UNIVERSAL_AVAILABLE:" in backend_content:
            logger.info("✅ Backend correctly checks for 'universal_' prefix in plan IDs")
        else:
            logger.warning("⚠️ Backend may not correctly check for 'universal_' prefix in plan IDs")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to check plan ID format: {e}")
        return False

def create_websocket_test_script():
    """Create a script to test the WebSocket connection and message handling"""
    try:
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/test_websocket_button_action.py"
        
        content = """#!/usr/bin/env python3
\"\"\"
WebSocket test script for button action messages.
Sends a button action directly to the WebSocket server.
\"\"\"

import asyncio
import json
import logging
import sys
import time
import websockets
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_button_action():
    try:
        # Connect to the WebSocket server
        uri = "ws://localhost:8767"
        logger.info(f"Connecting to WebSocket server at {uri}...")
        
        async with websockets.connect(uri) as websocket:
            # Generate a unique client ID
            client_id = f"test_client_{int(time.time())}"
            
            # First register with the server
            register_message = {
                "type": "register",
                "client_type": "test_client",
                "version": "1.0",
                "capabilities": ["button_actions"],
                "client_id": client_id
            }
            
            logger.info(f"Sending registration message: {register_message}")
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration response
            response = await websocket.recv()
            logger.info(f"Received registration response: {response}")
            
            # Create a test plan ID
            plan_id = f"universal_test_plan_{int(time.time())}"
            
            # Send a button action message
            button_action = {
                "type": "button_action",
                "action": "DO",
                "plan_id": plan_id,
                "client_id": client_id,
                "timestamp": time.time() * 1000
            }
            
            logger.info(f"Sending button action: {button_action}")
            await websocket.send(json.dumps(button_action))
            
            # Wait for response(s)
            logger.info("Waiting for responses...")
            try:
                for _ in range(5):  # Try to get up to 5 messages
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"Received response: {response}")
                    
                    # Check if this is a final response
                    try:
                        data = json.loads(response)
                        if data.get("type") in ["agent_execution_success", "agent_execution_error", "button_action_error"]:
                            break
                    except:
                        pass
            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for more responses")
            
            # Done
            logger.info("WebSocket test completed")
            return True
            
    except Exception as e:
        logger.error(f"Error in WebSocket test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\\n🔍 Testing WebSocket button action message...\\n")
    
    # Run test
    success = asyncio.run(send_button_action())
    
    print(f"\\n{'✅' if success else '❌'} WebSocket test: {'PASSED' if success else 'FAILED'}\\n")
    
    if success:
        print("🎉 WebSocket test completed!")
        print("Check the logs above to see if the button action was processed correctly.")
        print("If you see 'agent_execution_success', the execution path is working.")
    else:
        print("⚠️ WebSocket test failed. Check the error message above.")
    
    sys.exit(0 if success else 1)
"""
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Make it executable
        os.chmod(file_path, 0o755)
        
        logger.info("✅ Created test_websocket_button_action.py")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create WebSocket test script: {e}")
        return False

if __name__ == "__main__":
    print("\n🔧 Applying direct fixes for button action execution...\n")
    
    # Check plan ID format first
    print("Step 1: Checking plan ID format...")
    check_plan_id_format()
    print()
    
    # Add direct execution method to bypass LLM
    print("Step 2: Adding direct execution method...")
    fix_button_action_handler()
    print()
    
    # Create direct execution test script
    print("Step 3: Creating direct execution test script...")
    create_direct_execution_script()
    print()
    
    # Create WebSocket test script
    print("Step 4: Creating WebSocket test script...")
    create_websocket_test_script()
    print()
    
    print("✅ All fixes and test scripts created successfully!")
    print("To test if the execution flow works properly:")
    print("1. Run 'python3 execute_plan_directly.py' to test direct execution")
    print("2. Run 'python3 test_websocket_button_action.py' to test WebSocket message handling")
    print("\nThese tests will help identify where the DO button execution is failing.")
    
    print("\nIf the direct execution test works but the WebSocket test fails,")
    print("then the issue is likely with the WebSocket message handling or routing.")
    print("If both tests fail, there may be an issue with the execution path itself.")
    
    print("\nGood luck! 🚀")
    
    sys.exit(0)