#!/usr/bin/env python3
"""
Comprehensive test for DO button with all supported message formats.
This test sends all three message types that should trigger the DO button functionality.
"""
import asyncio
import websockets
import json
import time
import sys
import argparse
from datetime import datetime

# Configure command line arguments
parser = argparse.ArgumentParser(description="Test the DO button WebSocket server")
parser.add_argument("--url", default="ws://localhost:8765", help="WebSocket server URL")
parser.add_argument("--format", choices=["all", "agent_confirmation", "button_action", "do_button"], 
                   default="all", help="Message format to test (default: all)")
parser.add_argument("--debug", action="store_true", help="Enable debug output")
args = parser.parse_args()

# Define colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

async def test_message_format(ws, format_type, session_id):
    """Test a specific DO button message format"""
    print(f"{BLUE}🧪 Testing message format: {format_type}{RESET}")
    
    # Create appropriate message based on format type
    if format_type == "agent_confirmation":
        message = {
            "type": "agent_confirmation",
            "session_id": f"{session_id}_{format_type}",
            "action": "DO",
            "timestamp": datetime.now().isoformat()
        }
    elif format_type == "button_action":
        message = {
            "type": "button_action",
            "plan_id": f"{session_id}_{format_type}",
            "action": "EXECUTE_PLAN",
            "timestamp": datetime.now().isoformat()
        }
    elif format_type == "do_button":
        message = {
            "type": "do_button",
            "session_id": f"{session_id}_{format_type}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        print(f"{RED}❌ Unknown format type: {format_type}{RESET}")
        return False
    
    # Send the message
    print(f"{BLUE}📤 Sending message:{RESET}")
    if args.debug:
        print(json.dumps(message, indent=2))
    else:
        print(f"  Type: {message['type']}")
        if "session_id" in message:
            print(f"  Session ID: {message['session_id']}")
        elif "plan_id" in message:
            print(f"  Plan ID: {message['plan_id']}")
            
    await ws.send(json.dumps(message))
    
    # Collect responses
    progress_updates = []
    final_result = None
    
    # Wait for responses with a timeout
    try:
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout for the whole test
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(response)
            msg_type = data.get("type")
            
            if args.debug:
                print(f"{BLUE}📥 Received:{RESET} {json.dumps(data, indent=2)}")
            
            if msg_type == "agent_progress":
                progress = data.get("progress", 0)
                message = data.get("message", "No message")
                step = data.get("step", 0)
                progress_updates.append((step, progress, message))
                print(f"{YELLOW}📊 Progress: {progress}% - Step {step}: {message}{RESET}")
            
            elif msg_type == "agent_execution_success":
                final_result = data
                success = data.get("result", {}).get("success", False)
                summary = data.get("summary", "No summary")
                print(f"{GREEN}✅ Execution completed: {'SUCCESS' if success else 'FAILED'}{RESET}")
                print(f"{GREEN}📋 Summary: {summary}{RESET}")
                break
            
            elif msg_type == "agent_execution_error":
                final_result = data
                error = data.get("error", "Unknown error")
                print(f"{RED}❌ Execution failed: {error}{RESET}")
                break
            
            elif msg_type in ["agent_dismissed", "agent_adjustment_request"]:
                final_result = data
                print(f"{BLUE}ℹ️ Received {msg_type}: {data.get('message', '')}{RESET}")
                break
            
            elif msg_type == "response" or msg_type == "error":
                print(f"{YELLOW}⚠️ Server sent {msg_type}: {data.get('message', '')}{RESET}")
                final_result = data
                break
    
    except asyncio.TimeoutError:
        print(f"{YELLOW}⚠️ Timeout waiting for more responses{RESET}")
    
    # Print summary for this format
    success = False
    if final_result:
        result_type = final_result.get("type", "unknown")
        success = result_type == "agent_execution_success"
        
        print(f"\n{BLUE}🔍 Test Results for {format_type}:{RESET}")
        print(f"  Format: {format_type}")
        print(f"  Progress Updates: {len(progress_updates)}")
        print(f"  Final Status: {GREEN+'SUCCESS'+RESET if success else RED+'FAILED'+RESET}")
        
        if success:
            print(f"  Execution Time: {final_result.get('result', {}).get('execution_time', 0)}s")
            print(f"  Steps Executed: {final_result.get('result', {}).get('steps_executed', 0)}")
        else:
            print(f"  Response Type: {result_type}")
    else:
        print(f"{RED}❌ No final result received for {format_type}{RESET}")
    
    return success

async def run_comprehensive_test():
    """Run tests for all specified message formats"""
    print(f"{BLUE}🚀 Starting DO Button WebSocket test suite{RESET}")
    print(f"{BLUE}🔌 Connecting to: {args.url}{RESET}")
    
    results = {}
    session_id = f"test_{int(time.time())}"
    
    try:
        async with websockets.connect(args.url) as ws:
            # Get welcome message
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            print(f"{GREEN}✅ Connected to server: {welcome_data.get('message', 'Unknown')}{RESET}")
            
            # Determine which formats to test
            formats_to_test = ["agent_confirmation", "button_action", "do_button"] \
                if args.format == "all" else [args.format]
            
            # Test each format with a delay between tests
            for format_type in formats_to_test:
                results[format_type] = await test_message_format(ws, format_type, session_id)
                
                # Add a delay between tests to allow server to process
                if format_type != formats_to_test[-1]:
                    print(f"{BLUE}⏱️ Waiting 3 seconds before next test...{RESET}")
                    await asyncio.sleep(3)
    
    except websockets.exceptions.ConnectionError as e:
        print(f"{RED}❌ Connection error: {e}{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Unexpected error: {e}{RESET}")
        return False
    
    # Print final summary
    print(f"\n{BLUE}📊 Test Summary:{RESET}")
    all_passed = True
    for format_type, success in results.items():
        status = f"{GREEN}PASSED{RESET}" if success else f"{RED}FAILED{RESET}"
        print(f"  {format_type}: {status}")
        all_passed = all_passed and success
    
    if all_passed:
        print(f"\n{GREEN}✅ All tests passed!{RESET}")
    else:
        print(f"\n{RED}❌ Some tests failed.{RESET}")
    
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(130)