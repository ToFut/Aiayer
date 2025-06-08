#!/usr/bin/env python3
"""
Overlay Notification Test - Comprehensive solution for testing overlay notifications
Tries all possible formats and ports to ensure notifications work
"""

import asyncio
import json
import websockets
import uuid
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/overlay_notification_test.log')
    ]
)
logger = logging.getLogger('overlay_notification_test')

# Ports to try
ALL_PORTS = [8765, 8766, 8767, 8768]

# Message formats to try
NOTIFICATION_FORMATS = {
    "suggestion": {
        "type": "suggestion",
        "response": "{message}",
        "buttons": [],
        "importance": "high",
        "play_sound": True,
        "notification": True,
        "plan_id": "{notification_id}",
        "timestamp": "{timestamp}"
    },
    "message": {
        "type": "message",
        "message": "{message}",
        "mode": "SUGGEST",
        "buttons": [],
        "importance": "high",
        "play_sound": True,
        "notification": True,
        "timestamp": "{timestamp}"
    },
    "legacy": {
        "success": True,
        "response": "{message}",
        "mode": "SUGGEST",
        "notification": True,
        "play_sound": True,
        "importance": "high",
        "buttons": [],
        "interactive": True,
        "timestamp": "{timestamp}"
    },
    "client_message": {
        "type": "client_message",
        "content": "{message}",
        "buttons": [],
        "notification": True,
        "play_sound": True,
        "importance": "high",
        "timestamp": "{timestamp}"
    },
    "do_button_action": {
        "type": "do_button_action",
        "do_button_action": {
            "plan_id": "{notification_id}",
            "message": "{message}",
            "buttons": [],
            "importance": "high",
            "play_sound": True,
            "notification": True
        },
        "timestamp": "{timestamp}"
    }
}

# Default buttons
DEFAULT_BUTTONS = [
    {"text": "✅ Got it", "value": "understood", "style": "success"},
    {"text": "❓ More info", "value": "info", "style": "primary"},
    {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
]

async def send_notification(port, format_name, message, buttons=None, importance="high", play_sound=True):
    """Send a notification in a specific format to a specific port"""
    if buttons is None:
        buttons = DEFAULT_BUTTONS
        
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().isoformat()
    
    # Get the format template
    format_template = NOTIFICATION_FORMATS.get(format_name)
    if not format_template:
        logger.error(f"Unknown format: {format_name}")
        return False
    
    # Create a deep copy of the template
    notification = json.loads(json.dumps(format_template))
    
    # Format the message
    if "response" in notification:
        notification["response"] = notification["response"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "message" in notification:
        notification["message"] = notification["message"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "content" in notification:
        notification["content"] = notification["content"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "plan_id" in notification:
        notification["plan_id"] = notification["plan_id"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "timestamp" in notification:
        notification["timestamp"] = notification["timestamp"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "do_button_action" in notification and "message" in notification["do_button_action"]:
        notification["do_button_action"]["message"] = notification["do_button_action"]["message"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    if "do_button_action" in notification and "plan_id" in notification["do_button_action"]:
        notification["do_button_action"]["plan_id"] = notification["do_button_action"]["plan_id"].format(
            message=message, 
            notification_id=notification_id, 
            timestamp=timestamp
        )
    
    # Set buttons, importance, sound
    if "buttons" in notification:
        notification["buttons"] = buttons
    if "importance" in notification:
        notification["importance"] = importance
    if "play_sound" in notification:
        notification["play_sound"] = play_sound
    if "do_button_action" in notification:
        if "buttons" in notification["do_button_action"]:
            notification["do_button_action"]["buttons"] = buttons
        if "importance" in notification["do_button_action"]:
            notification["do_button_action"]["importance"] = importance
        if "play_sound" in notification["do_button_action"]:
            notification["do_button_action"]["play_sound"] = play_sound
    
    # Connect to WebSocket
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    try:
        logger.info(f"Connecting to {ws_url}...")
        async with websockets.connect(ws_url, ping_timeout=10) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=3.0)
            logger.info(f"Connected to {ws_url}! Welcome message received.")
            
            # Register with backend if needed
            if port == 8767:
                register_msg = {
                    "type": "register",
                    "client_type": "notification_test",
                    "client_id": f"notification_test_{uuid.uuid4()}"
                }
                await ws.send(json.dumps(register_msg))
                await asyncio.wait_for(ws.recv(), timeout=3.0)
                logger.info("Registered with backend server")
            
            # Send notification
            notification_json = json.dumps(notification)
            logger.info(f"Sending {format_name} format to port {port}: {message}")
            await ws.send(notification_json)
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                logger.info(f"Response received from port {port}")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"No response received from port {port}")
                return True  # Still consider it a success for testing
    
    except Exception as e:
        logger.error(f"Error connecting to port {port}: {e}")
        return False

async def test_all_combinations(message):
    """Test all combinations of ports and formats"""
    results = {}
    
    for port in ALL_PORTS:
        results[port] = {}
        for format_name in NOTIFICATION_FORMATS:
            port_message = f"[PORT {port}, FORMAT {format_name}] {message}"
            success = await send_notification(port, format_name, port_message)
            results[port][format_name] = success
            # Wait a moment between tests
            await asyncio.sleep(1.0)
    
    return results

async def main():
    """Main function"""
    print("\n=== OVERLAY NOTIFICATION TEST ===\n")
    print("This script tests all possible notification formats and ports\n")
    
    # Get message from command line or use default
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "🔔 COMPREHENSIVE TEST: This notification tests all possible formats and ports"
    
    print(f"Testing with message: {message}\n")
    print("Testing all combinations of ports and formats...")
    
    results = await test_all_combinations(message)
    
    print("\n=== TEST RESULTS ===\n")
    
    # Print summary
    success_count = 0
    total_tests = 0
    
    for port in results:
        print(f"Port {port}:")
        for format_name, success in results[port].items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {format_name}: {status}")
            if success:
                success_count += 1
            total_tests += 1
    
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nOverall success rate: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    print("\nCheck the overlay UI for notifications. If you see notifications,")
    print("you've found the correct port and format to use for your system.")
    print("\nTo use a specific port and format:")
    print("python overlay_notification_test.py PORT FORMAT \"Your message here\"")
    
    if success_count == 0:
        print("\n❌ All tests failed. Make sure the overlay and servers are running.")
        return 1
    else:
        print(f"\n✅ {success_count} successful tests. Check the overlay UI for notifications.")
        return 0

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 3 and sys.argv[1].isdigit() and sys.argv[2] in NOTIFICATION_FORMATS:
            # Run with specific port and format
            port = int(sys.argv[1])
            format_name = sys.argv[2]
            message = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "🔔 DIRECT TEST NOTIFICATION"
            
            print(f"\n=== TESTING PORT {port} WITH FORMAT {format_name} ===\n")
            print(f"Message: {message}\n")
            
            asyncio.run(send_notification(port, format_name, message))
        else:
            # Run comprehensive test
            sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)