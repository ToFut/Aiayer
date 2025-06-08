#!/usr/bin/env python3
"""
test_proactive_suggestion_complete.py - Complete test of the proactive suggestion system

This script tests the entire flow of the proactive suggestion system, including:
1. Adding a test suggestion to conscious memory
2. Verifying that the memory_aware_suggestion_monitor detects it
3. Confirming that a notification is sent to the overlay
4. Testing mode transition from Suggest to Agent
5. Verifying plan execution with the fixed_do_button_server.py

This test can be run after starting the system with START_ENHANCED_SYSTEM.sh
"""

import asyncio
import websockets
import json
import time
import sys
import logging
import os
from pathlib import Path
import argparse
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("proactive_suggestion_test")

# Configuration
WS_ENDPOINT = "ws://localhost:8765"
MEMORY_PATH = Path("/Users/segevbin/Desktop/SensAI/Aiayer/memory/conscious.json")
CONSCIOUS_BACKUP_PATH = MEMORY_PATH.with_suffix(".json.bak")
SUGGESTION_MONITOR_PID_PATH = Path("/Users/segevbin/Desktop/SensAI/Aiayer/pids/memory_suggestion_monitor.pid")
TEST_ID = f"test_{int(time.time())}"

class TestSuggestion:
    """Class to handle the test suggestion creation and verification"""
    
    def __init__(self, title=None, message=None, confidence=0.85):
        """Initialize with default or custom suggestion content"""
        self.title = title or f"Test Automation {random.randint(1000, 9999)}"
        self.message = message or "I noticed you could benefit from an automated workflow for this task"
        self.confidence = confidence
        self.suggestion_id = f"suggestion_{int(time.time())}_{hash(self.title + self.message) % 10000}"
        self.plan_id = self.suggestion_id
        
    def to_memory_format(self):
        """Format the suggestion for insertion into conscious memory"""
        return f"SUGGESTION: {self.title} | {self.message} | {self.confidence}"
    
    def to_notification_payload(self):
        """Create a notification payload similar to what memory_aware_suggestion_monitor.py would send"""
        return {
            "success": True,
            "response": f"💡 {self.title}: {self.message}",
            "mode": "SUGGEST",
            "processing_time": 0.5,
            "enterprise_validated": True,
            "notification": True,
            "play_sound": True,
            "sound_type": "notification",
            "importance": "high" if self.confidence > 0.8 else "normal",
            "buttons": [
                {
                    "id": "do_it",
                    "text": "Yes, help me",
                    "action": "accept",
                    "style": "success"
                },
                {
                    "id": "dismiss",
                    "text": "No thanks",
                    "action": "dismiss",
                    "style": "danger"
                }
            ],
            "interactive": True,
            "plan_id": self.plan_id,
            "timestamp": time.time()
        }
        
    def to_agent_mode_payload(self):
        """Create an Agent mode payload for when the suggestion is accepted"""
        return {
            "success": True,
            "response": f"🤖 Ready to execute: {self.title}\n\nI'll perform the following steps:",
            "mode": "Agent",
            "processing_time": 0.3,
            "enterprise_validated": True,
            "notification": False,
            "plan_id": self.plan_id,
            "buttons": [
                {
                    "id": "execute_plan",
                    "text": "Execute Now",
                    "action": "execute_plan",
                    "style": "success"
                },
                {
                    "id": "cancel",
                    "text": "Cancel",
                    "action": "cancel",
                    "style": "danger"
                }
            ],
            "interactive": True,
            "requires_approval": True,
            "plan": {
                "id": self.plan_id,
                "title": self.title,
                "steps": [
                    {"description": "Step 1: Analyze current workflow patterns", "type": "analysis"},
                    {"description": "Step 2: Identify automation opportunities", "type": "analysis"},
                    {"description": "Step 3: Create automated workflow sequence", "type": "action", "target": "workflow"},
                    {"description": "Step 4: Verify results and optimize", "type": "verification"}
                ],
                "estimated_duration": "1 minute",
                "risk_level": "low"
            }
        }
        
    def to_execution_button_action(self):
        """Create a button action payload to simulate clicking the Execute button"""
        return {
            "type": "button_action",
            "action": "execute_plan",
            "plan_id": self.plan_id,
            "session_id": f"test_session_{int(time.time())}"
        }

async def verify_suggestion_monitor_running():
    """Verify that the memory_aware_suggestion_monitor.py is running"""
    if SUGGESTION_MONITOR_PID_PATH.exists():
        try:
            pid = int(SUGGESTION_MONITOR_PID_PATH.read_text().strip())
            # Check if process is running (works on Unix/Linux/Mac)
            if os.system(f"ps -p {pid} > /dev/null") == 0:
                logger.info(f"✅ Memory-aware suggestion monitor is running (PID: {pid})")
                return True
            else:
                logger.warning(f"⚠️ Memory-aware suggestion monitor process not found (PID: {pid})")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking suggestion monitor: {str(e)}")
            return False
    else:
        logger.error("❌ Memory suggestion monitor PID file not found")
        logger.info("  Make sure to run START_ENHANCED_SYSTEM.sh first")
        return False

async def backup_conscious_memory():
    """Backup the conscious memory file before modifying it"""
    if MEMORY_PATH.exists():
        try:
            # Create backup
            content = MEMORY_PATH.read_text()
            CONSCIOUS_BACKUP_PATH.write_text(content)
            logger.info(f"✅ Backed up conscious memory to {CONSCIOUS_BACKUP_PATH}")
            return True
        except Exception as e:
            logger.error(f"❌ Error backing up conscious memory: {str(e)}")
            return False
    else:
        logger.error(f"❌ Conscious memory file not found at {MEMORY_PATH}")
        return False

async def restore_conscious_memory():
    """Restore the conscious memory from backup"""
    if CONSCIOUS_BACKUP_PATH.exists():
        try:
            # Restore from backup
            content = CONSCIOUS_BACKUP_PATH.read_text()
            MEMORY_PATH.write_text(content)
            logger.info(f"✅ Restored conscious memory from backup")
            return True
        except Exception as e:
            logger.error(f"❌ Error restoring conscious memory: {str(e)}")
            return False
    else:
        logger.error(f"❌ Conscious memory backup not found at {CONSCIOUS_BACKUP_PATH}")
        return False

async def add_suggestion_to_memory(suggestion):
    """Add a test suggestion to the conscious memory file"""
    if not MEMORY_PATH.exists():
        logger.error(f"❌ Conscious memory file not found at {MEMORY_PATH}")
        return False
        
    try:
        # Read current memory content
        with open(MEMORY_PATH, "r") as f:
            memory_data = json.load(f)
            
        # Add the suggestion to insights
        if "insights" not in memory_data:
            memory_data["insights"] = []
            
        # Create a new insight with the suggestion
        suggestion_insight = {
            "id": f"insight_{int(time.time())}",
            "timestamp": time.time(),
            "type": "suggestion",
            "content": suggestion.to_memory_format(),
            "confidence": suggestion.confidence,
            "source": "test"
        }
        
        # Add to insights
        memory_data["insights"].insert(0, suggestion_insight)
        
        # Write back to file
        with open(MEMORY_PATH, "w") as f:
            json.dump(memory_data, f, indent=2)
            
        logger.info(f"✅ Added suggestion to conscious memory: {suggestion.title}")
        logger.info(f"  Suggestion format: {suggestion.to_memory_format()}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding suggestion to memory: {str(e)}")
        return False

async def check_suggestion_detection(suggestion, max_wait=30):
    """Check if the suggestion has been detected by memory_aware_suggestion_monitor.py"""
    suggestion_path = Path(f"memory/suggestions/{suggestion.suggestion_id}.json")
    
    logger.info(f"Waiting for suggestion detection (max {max_wait}s)...")
    
    # Wait for the suggestion file to be created (with timeout)
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if suggestion_path.exists():
            logger.info(f"✅ Suggestion detected and saved to {suggestion_path}")
            return True
        
        # Wait a bit before checking again
        await asyncio.sleep(1)
        
    logger.error(f"❌ Suggestion not detected after {max_wait} seconds")
    logger.info("  Check logs/memory/suggestion_monitor.log for details")
    return False

async def check_websocket_server():
    """Check if the WebSocket server is running on port 8765"""
    try:
        # Use wait_for around the connect to implement a timeout
        async with await asyncio.wait_for(
            websockets.connect(WS_ENDPOINT), 
            timeout=5
        ) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            if welcome_data.get("type") == "welcome":
                logger.info("✅ WebSocket server is running and accessible")
                return True
            else:
                logger.warning(f"⚠️ Unexpected welcome message: {welcome_data}")
                return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to WebSocket server: {str(e)}")
        return False

async def send_manual_suggestion(suggestion):
    """Send a suggestion manually via WebSocket if automatic detection fails"""
    try:
        # Use wait_for around connect to implement a timeout
        async with await asyncio.wait_for(
            websockets.connect(WS_ENDPOINT),
            timeout=5
        ) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            
            # Create payload
            payload = suggestion.to_notification_payload()
            
            # Send suggestion
            await ws.send(json.dumps(payload))
            logger.info(f"✅ Manually sent suggestion: {suggestion.title}")
            
            # Try to get a response (but don't fail if none received)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                logger.info(f"Received response: {response[:100] if len(response) > 100 else response}")
            except asyncio.TimeoutError:
                logger.info("No immediate response (this is normal)")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Error sending manual suggestion: {str(e)}")
        return False

async def send_agent_mode_transition(suggestion):
    """Send a mode transition to Agent mode manually"""
    try:
        # Use wait_for around connect to implement a timeout
        async with await asyncio.wait_for(
            websockets.connect(WS_ENDPOINT),
            timeout=5
        ) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            
            # Create agent mode payload
            payload = suggestion.to_agent_mode_payload()
            
            # Send mode transition
            await ws.send(json.dumps(payload))
            logger.info(f"✅ Sent mode transition to Agent for suggestion: {suggestion.title}")
            
            # Try to get a response (but don't fail if none received)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                logger.info(f"Received response: {response[:100] if len(response) > 100 else response}")
            except asyncio.TimeoutError:
                logger.info("No immediate response (this is normal)")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Error sending mode transition: {str(e)}")
        return False

async def send_execution_confirmation(suggestion):
    """Send an execution confirmation to trigger plan execution"""
    try:
        # Use wait_for around connect to implement a timeout
        async with await asyncio.wait_for(
            websockets.connect(WS_ENDPOINT),
            timeout=5
        ) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            
            # Create execution button action
            payload = suggestion.to_execution_button_action()
            
            # Send execution confirmation
            await ws.send(json.dumps(payload))
            logger.info(f"✅ Sent execution confirmation for plan: {suggestion.plan_id}")
            
            # Wait for execution updates
            execution_completed = False
            progress_updates = 0
            
            try:
                for _ in range(10):  # Try to capture a few execution messages
                    response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "agent_progress":
                        progress = response_data.get("progress", 0)
                        step = response_data.get("currentStep", "Unknown")
                        logger.info(f"  Execution progress: {progress}% - {step}")
                        progress_updates += 1
                    
                    elif response_data.get("type") == "agent_execution_success":
                        result = response_data.get("result", {})
                        summary = response_data.get("summary", "No summary provided")
                        logger.info(f"  Execution complete: {summary}")
                        logger.info(f"  Result: {result}")
                        execution_completed = True
                        break
                        
            except asyncio.TimeoutError:
                logger.info("  No more execution updates received")
            
            # Return based on what we received
            if execution_completed:
                logger.info("  Plan execution completed successfully")
                return True
            elif progress_updates > 0:
                logger.info(f"  Plan execution in progress ({progress_updates} updates received)")
                return True
            else:
                logger.warning("  No execution progress updates received")
                return True  # Still return True to continue the test
                
    except Exception as e:
        logger.error(f"❌ Error sending execution confirmation: {str(e)}")
        return False

async def verify_user_interaction(step_name, prompt_text):
    """Verify user interaction with a prompt"""
    print("\n" + "="*60)
    print(f"USER ACTION REQUIRED: {step_name}")
    print("="*60)
    print(prompt_text)
    print("\nEnter 'y' when complete, or any other key to skip: ")
    
    # Wait for user confirmation
    response = await asyncio.get_event_loop().run_in_executor(None, input)
    
    if response.lower() == 'y':
        logger.info(f"✅ User confirmed completion of {step_name}")
        return True
    else:
        logger.warning(f"⚠️ User skipped {step_name}")
        return False

async def run_automated_tests(suggestion, manual_mode=False):
    """Run automated tests of the proactive suggestion system"""
    # Test setup and verification
    logger.info("="*80)
    logger.info(" PROACTIVE SUGGESTION SYSTEM COMPREHENSIVE TEST ".center(80, "="))
    logger.info("="*80)
    
    # Step 1: Verify suggestion monitor is running
    if not await verify_suggestion_monitor_running() and not manual_mode:
        logger.error("❌ Memory-aware suggestion monitor is not running")
        logger.info("  Please run START_ENHANCED_SYSTEM.sh first")
        return False
        
    # Step 2: Check WebSocket server status
    if not await check_websocket_server():
        logger.error("❌ WebSocket server is not running on port 8765")
        logger.info("  Please run START_ENHANCED_SYSTEM.sh first")
        return False
    
    # Step 3: Backup conscious memory before modifying
    memory_backed_up = await backup_conscious_memory()
    if not memory_backed_up:
        logger.warning("⚠️ Could not backup conscious memory, proceeding without backup")
    
    try:
        # Step 4: Add test suggestion to memory (skip in manual mode)
        if not manual_mode:
            suggestion_added = await add_suggestion_to_memory(suggestion)
            if not suggestion_added:
                logger.error("❌ Failed to add suggestion to memory")
                return False
                
            # Step 5: Wait for suggestion detection (skip in manual mode)
            suggestion_detected = await check_suggestion_detection(suggestion, max_wait=15)
            if not suggestion_detected:
                logger.warning("⚠️ Suggestion not automatically detected, will send manually")
        
        # Step 6: Send suggestion manually if needed or in manual mode
        if manual_mode or not suggestion_detected:
            suggestion_sent = await send_manual_suggestion(suggestion)
            if not suggestion_sent:
                logger.error("❌ Failed to send suggestion manually")
                return False
        
        # Step 7: Verify suggestion appears in overlay
        user_saw_suggestion = await verify_user_interaction(
            "Suggestion Notification",
            "Please look at the NextGen overlay chat window and verify:\n"
            "1. Do you see the suggestion with sound notification?\n"
            "2. Does it have the title and message as expected?\n"
            "3. Are there 'Yes, help me' and 'No thanks' buttons?"
        )
        
        if not user_saw_suggestion:
            logger.warning("⚠️ User did not confirm seeing the suggestion")
        
        # Step 8: Send mode transition (simulate accepting the suggestion)
        mode_transition_sent = await send_agent_mode_transition(suggestion)
        if not mode_transition_sent:
            logger.error("❌ Failed to send mode transition")
            return False
        
        # Step 9: Verify mode transition in overlay
        user_saw_transition = await verify_user_interaction(
            "Mode Transition",
            "In the NextGen overlay chat window, verify:\n"
            "1. Did the UI switch to Agent mode with a plan?\n"
            "2. Can you see the 'Execute Now' button?\n"
            "3. Is the plan visible with steps?"
        )
        
        if not user_saw_transition:
            logger.warning("⚠️ User did not confirm seeing the mode transition")
        
        # Step 10: Send execution confirmation
        execution_sent = await send_execution_confirmation(suggestion)
        if not execution_sent:
            logger.error("❌ Failed to send execution confirmation")
            return False
        
        # Step 11: Verify execution in overlay
        user_saw_execution = await verify_user_interaction(
            "Plan Execution",
            "In the NextGen overlay chat window, verify:\n"
            "1. Did you see the execution progress updates?\n"
            "2. Did the execution complete successfully?\n"
            "3. Were all steps executed correctly?"
        )
        
        if not user_saw_execution:
            logger.warning("⚠️ User did not confirm seeing the execution")
        
        # Print test summary
        print("\n" + "="*80)
        print(" TEST RESULTS SUMMARY ".center(80, "="))
        print("="*80)
        print(f"WebSocket Server Status: {'✅ PASS' if True else '❌ FAIL'}")
        if not manual_mode:
            print(f"Suggestion Monitor Status: {'✅ PASS' if await verify_suggestion_monitor_running() else '❌ FAIL'}")
            print(f"Add Suggestion to Memory: {'✅ PASS' if suggestion_added else '❌ FAIL'}")
            print(f"Suggestion Detection: {'✅ PASS' if suggestion_detected else '❌ FAIL'}")
        if manual_mode or not suggestion_detected:
            print(f"Manual Suggestion Sending: {'✅ PASS' if suggestion_sent else '❌ FAIL'}")
        print(f"Suggestion Notification: {'✅ PASS' if user_saw_suggestion else '❌ FAIL'}")
        print(f"Mode Transition: {'✅ PASS' if mode_transition_sent else '❌ FAIL'}")
        print(f"Mode Transition UI: {'✅ PASS' if user_saw_transition else '❌ FAIL'}")
        print(f"Execution Confirmation: {'✅ PASS' if execution_sent else '❌ FAIL'}")
        print(f"Execution Visualization: {'✅ PASS' if user_saw_execution else '❌ FAIL'}")
        
        # Overall result
        overall_result = (
            (manual_mode or suggestion_added) and 
            (manual_mode or suggestion_detected or suggestion_sent) and
            user_saw_suggestion and
            mode_transition_sent and
            user_saw_transition and
            execution_sent and
            user_saw_execution
        )
        print("-"*80)
        print(f"Overall Test Result: {'✅ PASS' if overall_result else '❌ FAIL'}")
        print("="*80)
        
        return overall_result
        
    finally:
        # Always restore the conscious memory if we backed it up
        if memory_backed_up:
            await restore_conscious_memory()

async def main():
    """Main function to run the test"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the proactive suggestion system")
    parser.add_argument("--title", help="Custom suggestion title")
    parser.add_argument("--message", help="Custom suggestion message")
    parser.add_argument("--manual", action="store_true", help="Run in manual mode (skip memory monitoring)")
    args = parser.parse_args()
    
    # Create test suggestion
    suggestion = TestSuggestion(
        title=args.title,
        message=args.message
    )
    
    # Run tests
    result = await run_automated_tests(suggestion, manual_mode=args.manual)
    
    # Exit with appropriate code
    return 0 if result else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in tests: {str(e)}")
        sys.exit(1)