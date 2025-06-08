#!/usr/bin/env python3
"""
Comprehensive test script for the complete DO button fix chain
This script tests the entire flow from plan creation to execution
with the new plan persistence proxy in place.
"""

import json
import time
import websocket
import threading
import logging
import os
import uuid
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DO_BUTTON_FIX_TEST")

# WebSocket endpoints
BRAIN_ROUTER_WS = "ws://localhost:8767"
OVERLAY_WS = "ws://localhost:8765"
DO_BUTTON_WS = "ws://localhost:8766"  # Connect to our new proxy

# Test parameters
NUM_TESTS = 3
TEST_TIMEOUT = 120  # seconds
TEST_DELAY = 5  # seconds between tests

# Results tracking
results = {
    "tests": [],
    "overall_success": False,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

class TestCase:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.session_id = f"overlay_session_{int(time.time() * 1000)}"
        self.task_id = f"task_{int(time.time())}"
        self.full_session_id = f"{self.task_id}_{self.session_id}"
        self.plan_created = False
        self.plan_executed = False
        self.errors = []
        self.success = False
        self.messages = []
        self.plan_id = None
        self.start_time = None
        self.end_time = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}"
        logger.info(f"[{self.name}] {message}")
        self.messages.append(formatted_message)
        
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "full_session_id": self.full_session_id,
            "plan_created": self.plan_created,
            "plan_executed": self.plan_executed,
            "success": self.success,
            "errors": self.errors,
            "messages": self.messages,
            "plan_id": self.plan_id,
            "duration": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None
        }

def create_brain_router_client(test_case):
    """Create a WebSocket client connected to the brain router"""
    brain_ws = websocket.WebSocketApp(
        BRAIN_ROUTER_WS,
        on_open=lambda ws: on_brain_open(ws, test_case),
        on_message=lambda ws, msg: on_brain_message(ws, msg, test_case),
        on_error=lambda ws, err: on_brain_error(ws, err, test_case),
        on_close=lambda ws, close_status_code, close_msg: on_brain_close(ws, close_status_code, close_msg, test_case)
    )
    return brain_ws

def on_brain_open(ws, test_case):
    test_case.log(f"Connected to Brain Router on {BRAIN_ROUTER_WS}")
    # Send a message to create a plan
    query = "What can I do with Google Chrome?"
    message = {
        "type": "agent",
        "sessionId": test_case.full_session_id,
        "query": query
    }
    test_case.log(f"Sending agent request: '{query}'")
    ws.send(json.dumps(message))

def on_brain_message(ws, message, test_case):
    try:
        data = json.loads(message)
        msg_type = data.get("type", "unknown")
        
        if "error" in data:
            test_case.log(f"Error from Brain Router: {data['error']}")
            test_case.errors.append(f"Brain Router error: {data['error']}")
            return
            
        if msg_type == "plan":
            test_case.plan_created = True
            test_case.plan_id = data.get("planId")
            test_case.log(f"Plan created with ID: {test_case.plan_id}")
            
            # After plan is created, initiate DO button click
            threading.Timer(2.0, test_do_button_click, args=[test_case]).start()
        
        elif msg_type == "agent_response":
            test_case.log(f"Got agent response: {data.get('response', '')[:100]}...")
            
    except Exception as e:
        test_case.log(f"Error processing brain message: {str(e)}")
        test_case.errors.append(f"Message processing error: {str(e)}")

def on_brain_error(ws, error, test_case):
    test_case.log(f"Brain Router WebSocket error: {str(error)}")
    test_case.errors.append(f"Brain Router connection error: {str(error)}")

def on_brain_close(ws, close_status_code, close_msg, test_case):
    test_case.log(f"Brain Router connection closed: {close_status_code} - {close_msg}")

def test_do_button_click(test_case):
    """Simulate clicking the DO button by sending a message to the DO button server"""
    try:
        test_case.log("Initiating DO button click...")
        do_ws = websocket.create_connection(DO_BUTTON_WS)
        
        message = {
            "type": "agent_confirmation",
            "sessionId": test_case.full_session_id,
            "action": "execute_plan"
        }
        
        test_case.log(f"Sending DO button request with session ID: {test_case.full_session_id}")
        do_ws.send(json.dumps(message))
        
        # Wait for response
        response = do_ws.recv()
        data = json.loads(response)
        
        if data.get("success") is True:
            test_case.plan_executed = True
            test_case.log(f"DO button request successful: {data.get('message', 'No message')}")
        else:
            error_msg = data.get("error", "Unknown error")
            test_case.log(f"DO button request failed: {error_msg}")
            test_case.errors.append(f"DO button execution failed: {error_msg}")
        
        do_ws.close()
        
        # Mark test as complete after a short delay
        threading.Timer(3.0, complete_test, args=[test_case]).start()
        
    except Exception as e:
        test_case.log(f"Error in DO button test: {str(e)}")
        test_case.errors.append(f"DO button connection error: {str(e)}")
        complete_test(test_case)

def complete_test(test_case):
    """Mark the test as complete and evaluate success"""
    test_case.end_time = datetime.now()
    
    # Test is successful if both plan was created and executed
    test_case.success = test_case.plan_created and test_case.plan_executed and len(test_case.errors) == 0
    
    if test_case.success:
        test_case.log("✅ TEST PASSED: Plan created and executed successfully")
    else:
        test_case.log("❌ TEST FAILED: See errors for details")
        if not test_case.plan_created:
            test_case.log("❌ Plan was not created")
        if not test_case.plan_executed:
            test_case.log("❌ Plan was not executed")
    
    # Add test case to results
    results["tests"].append(test_case.to_dict())
    
    # Check if all tests are complete
    if len(results["tests"]) == NUM_TESTS:
        finalize_results()

def finalize_results():
    """Finalize and save test results"""
    # Check if all tests were successful
    results["overall_success"] = all(test["success"] for test in results["tests"])
    
    # Add summary stats
    results["summary"] = {
        "total_tests": len(results["tests"]),
        "successful_tests": sum(1 for test in results["tests"] if test["success"]),
        "failed_tests": sum(1 for test in results["tests"] if not test["success"]),
    }
    
    # Save results to file
    timestamp = int(time.time())
    results_file = f"test_do_button_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {results_file}")
    
    # Print summary
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total tests: {results['summary']['total_tests']}")
    logger.info(f"Successful: {results['summary']['successful_tests']}")
    logger.info(f"Failed: {results['summary']['failed_tests']}")
    
    if results["overall_success"]:
        logger.info("✅ ALL TESTS PASSED")
        logger.info("The DO Button fix has been successfully implemented!")
    else:
        logger.info("❌ SOME TESTS FAILED")
        logger.info("Check the detailed results for more information")
    
    logger.info("=" * 50)

def run_tests():
    """Run the specified number of test cases"""
    logger.info("=" * 50)
    logger.info("STARTING DO BUTTON FIX VERIFICATION TESTS")
    logger.info("=" * 50)
    logger.info(f"Running {NUM_TESTS} test iterations...")
    
    for i in range(NUM_TESTS):
        test_name = f"DO_Button_Test_{i+1}"
        test_description = f"Testing DO button plan persistence and execution, iteration {i+1}"
        
        # Create and start test case
        test_case = TestCase(test_name, test_description)
        test_case.start_time = datetime.now()
        test_case.log(f"Starting test with session ID: {test_case.full_session_id}")
        
        # Create and start WebSocket client in a separate thread
        brain_ws = create_brain_router_client(test_case)
        brain_thread = threading.Thread(target=brain_ws.run_forever)
        brain_thread.daemon = True
        brain_thread.start()
        
        # Add delay between tests
        if i < NUM_TESTS - 1:
            time.sleep(TEST_DELAY)

if __name__ == "__main__":
    try:
        # Ensure the system is running
        logger.info("Checking if the enhanced system is running...")
        ports_to_check = [8765, 8766, 8767]
        all_ports_open = True
        
        for port in ports_to_check:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(("localhost", port))
                s.close()
                logger.info(f"Port {port} is open and accepting connections")
            except:
                logger.error(f"Port {port} is not open. Make sure the system is running.")
                all_ports_open = False
        
        if not all_ports_open:
            logger.error("Some required services are not running. Please start the system using:")
            logger.error("./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh")
            exit(1)
            
        # Run the tests
        run_tests()
        
        # Wait for all tests to complete
        logger.info(f"Waiting up to {TEST_TIMEOUT} seconds for tests to complete...")
        timeout = time.time() + TEST_TIMEOUT
        while len(results["tests"]) < NUM_TESTS and time.time() < timeout:
            time.sleep(1)
        
        # If not all tests completed, finalize with what we have
        if len(results["tests"]) < NUM_TESTS:
            logger.warning(f"Test timeout reached. Only {len(results['tests'])} of {NUM_TESTS} tests completed.")
            finalize_results()
            
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user.")
        if results["tests"]:
            finalize_results()
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")