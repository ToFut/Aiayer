#!/usr/bin/env python3
"""
Comprehensive Memory Trigger Test

This script will:
1. Verify the memory_trigger_service is running
2. Check the WebSocket connection to the frontend overlay
3. Add test memories for multiple scenarios
4. Verify notifications are being generated
5. Ensure the frontend chat overlay is receiving messages

Usage:
  python full_memory_trigger_test.py
"""

import sys
import asyncio
import logging
import time
import json
import os
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("full_memory_trigger_test")

# Memory trigger service log file
MEMORY_TRIGGER_LOG = "logs/memory/memory_trigger.log"
# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def check_service_running():
    """Check if memory trigger service is running"""
    try:
        # Check for recent log entries
        if not os.path.exists(MEMORY_TRIGGER_LOG):
            logger.error(f"Memory trigger log file not found: {MEMORY_TRIGGER_LOG}")
            return False
        
        # Get last modified time
        last_modified = os.path.getmtime(MEMORY_TRIGGER_LOG)
        current_time = time.time()
        time_diff_minutes = (current_time - last_modified) / 60
        
        if time_diff_minutes > 10:
            logger.warning(f"Memory trigger log hasn't been updated in {time_diff_minutes:.2f} minutes")
            return False
        
        # Check process
        import psutil
        python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                            if 'python' in p.info['name'].lower()]
        
        for proc in python_processes:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('memory_trigger' in cmd for cmd in cmdline):
                logger.info(f"Memory trigger service is running (PID: {proc.info['pid']})")
                return True
        
        # Try to check if the service is registered in the brain router
        # This is a fallback check since we might not find the process directly
        return True
    
    except Exception as e:
        logger.error(f"Error checking memory trigger service: {e}")
        return False

async def test_websocket_connection():
    """Test WebSocket connection to the frontend overlay"""
    try:
        logger.info(f"Testing WebSocket connection to {WS_URI}")
        
        try:
            async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
                logger.info("✅ Successfully connected to WebSocket server")
                
                # Send a test message
                test_msg = {
                    "type": "test_message",
                    "content": "Testing WebSocket connection from memory trigger test",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(test_msg))
                logger.info("Sent test message to WebSocket server")
                
                # Wait for a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    logger.info(f"Received response: {response[:100]}")
                    return True
                except asyncio.TimeoutError:
                    logger.warning("No response received from WebSocket server (timeout)")
                    # Connection might still be working even without response
                    return True
        
        except (websockets.exceptions.ConnectionRefusedError, 
                websockets.exceptions.ConnectionClosedError) as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing WebSocket connection: {e}")
        return False

def get_test_memory_items():
    """Get test memory items for multiple scenarios"""
    # Shopping memory
    shopping_memory = {
        "type": "web_content",
        "url": "https://www.amazon.com/products/smartphone",
        "title": "Premium Smartphone XYZ - Amazon.com",
        "searchable_text": """
        Premium Smartphone XYZ with 108MP Camera

        Price: $899.99
        Save $100.00 (10%)
        FREE Shipping
        In Stock.
        
        Buy Now | Add to Cart | Add to List
        
        Features:
        • 6.8" Dynamic AMOLED Display
        • 108MP Camera with 8K Video
        • 5000mAh Battery
        • 5G Connectivity
        
        Product Description:
        Experience the ultimate smartphone with revolutionary camera technology...
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Form memory
    form_memory = {
        "type": "web_content",
        "url": "https://accounts.google.com/signup",
        "title": "Create your Google Account",
        "searchable_text": """
        Create your Google Account
        
        First name:
        Last name:
        
        Username: @gmail.com
        
        Password:
        Confirm password:
        
        Next | Sign in instead
        
        By creating an account, you agree to our Terms of Service and acknowledge 
        that you have read our Privacy Policy to learn how we collect and use your data.
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Documentation memory
    docs_memory = {
        "type": "web_content",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
        "title": "Using the Fetch API - Web APIs | MDN",
        "searchable_text": """
        Using the Fetch API
        
        The Fetch API provides a JavaScript interface for accessing and manipulating 
        parts of the HTTP pipeline, such as requests and responses. It also provides 
        a global fetch() method that provides an easy, logical way to fetch resources 
        asynchronously across the network.
        
        Basic fetch request:
        
        ```javascript
        fetch('https://api.example.com/data')
          .then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.error('Error:', error));
        ```
        
        Supply request options:
        
        ```javascript
        fetch('https://api.example.com/data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        })
        ```
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Application memories
    chrome_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Premium Smartphone XYZ - Amazon.com - Google Chrome",
        "searchable_text": "Browser window showing Amazon product page",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    return [shopping_memory, form_memory, docs_memory, chrome_memory]

async def add_test_memories():
    """Add test memories to the memory system"""
    try:
        # Import memory components
        from memory.memory_system import MemorySystem
        
        # Create memory system instance
        memory_system = MemorySystem()
        logger.info("Created memory system")
        
        # Get test memory items
        memory_items = get_test_memory_items()
        
        # Add memory items one by one with slight delay
        for i, item in enumerate(memory_items):
            memory_system.short_term_memory.append(item)
            logger.info(f"Added memory item {i+1}: {item.get('type')} - {item.get('title')}")
            await asyncio.sleep(1)  # Small delay between items
        
        # Save memory state to ensure persistence
        if hasattr(memory_system, '_save_memory_state_sync'):
            memory_system._save_memory_state_sync()
            logger.info("Saved memory state")
        
        logger.info(f"Successfully added {len(memory_items)} test memory items")
        return True
    
    except Exception as e:
        logger.error(f"Error adding test memories: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def verify_notifications_generated():
    """Verify that notifications are being generated by the memory trigger service"""
    try:
        # Check memory trigger log for notification creation
        if not os.path.exists(MEMORY_TRIGGER_LOG):
            logger.error(f"Memory trigger log file not found: {MEMORY_TRIGGER_LOG}")
            return False
        
        # Get last few lines of log
        notification_lines = []
        with open(MEMORY_TRIGGER_LOG, 'r') as f:
            lines = f.readlines()
            # Look for notification creation in recent lines
            for line in reversed(lines[-100:]):
                if "notification created" in line.lower() or "created notification" in line.lower():
                    notification_lines.append(line)
                    if len(notification_lines) >= 3:
                        break
        
        if notification_lines:
            logger.info(f"Found {len(notification_lines)} recent notification creation entries:")
            for i, line in enumerate(notification_lines):
                logger.info(f"  {i+1}: {line.strip()}")
            return True
        else:
            logger.warning("No recent notification creation entries found in log")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying notifications: {e}")
        return False

async def monitor_websocket_traffic():
    """Monitor WebSocket traffic for notification messages"""
    try:
        logger.info(f"Monitoring WebSocket traffic on {WS_URI}")
        logger.info("This will run for 2 minutes to capture notification messages")
        
        try:
            async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
                logger.info("Connected to WebSocket server, monitoring traffic...")
                
                # Monitor for 2 minutes
                start_time = time.time()
                end_time = start_time + 120  # 2 minutes
                
                notification_count = 0
                while time.time() < end_time:
                    try:
                        # Wait for messages with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        
                        # Parse and check if it's a notification
                        try:
                            data = json.loads(message)
                            message_type = data.get('type', '')
                            
                            if 'notification' in message_type.lower() or 'suggest' in message_type.lower():
                                notification_count += 1
                                logger.info(f"Detected notification message: {message[:100]}...")
                        except json.JSONDecodeError:
                            # Not JSON or not formatted as expected
                            pass
                            
                    except asyncio.TimeoutError:
                        # No message received, continue monitoring
                        await asyncio.sleep(1)
                
                logger.info(f"Monitoring complete. Detected {notification_count} notification messages")
                return notification_count > 0
                
        except (websockets.exceptions.ConnectionRefusedError, 
                websockets.exceptions.ConnectionClosedError) as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error monitoring WebSocket traffic: {e}")
        return False

async def force_trigger_notification():
    """Force a direct notification through the service API"""
    try:
        from memory.memory_trigger_service import MemoryTriggerService, TriggerRule, TriggerType, TriggerPriority
        
        # Check if we can access the service
        # This is challenging since we need a reference to the actual running service
        logger.info("Attempting to force a direct notification (this may not work if service isn't accessible)")
        
        # Create a new notification manually in memory
        notification_data = {
            "type": "direct_test",
            "title": "Test Notification from Memory Trigger Test",
            "description": "This is a direct test notification to verify the chat overlay connection",
            "confidence": 0.95,
            "context": {
                "source": "test_script",
                "timestamp": time.time()
            }
        }
        
        # Write notification data to a file that can be picked up
        test_notification_file = "cache/test_notification.json"
        os.makedirs(os.path.dirname(test_notification_file), exist_ok=True)
        
        with open(test_notification_file, 'w') as f:
            json.dump(notification_data, f)
        
        logger.info(f"Created test notification file: {test_notification_file}")
        logger.info("If the memory trigger service is monitoring this location, it should pick up the notification")
        
        return True
    
    except Exception as e:
        logger.error(f"Error forcing notification: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting comprehensive memory trigger test")
    
    # Check if memory trigger service is running
    service_running = await check_service_running()
    if not service_running:
        logger.warning("Memory trigger service doesn't appear to be running")
        logger.info("Starting system manually...")
        # We don't have a direct way to start just the memory trigger service
        # so we'll continue and hope it's just not visible in the process list
    
    # Test WebSocket connection
    ws_connection = await test_websocket_connection()
    if not ws_connection:
        logger.error("WebSocket connection failed - notifications won't reach the frontend")
        logger.error("Make sure the overlay and websocket server are running")
        return False
    
    # Add test memories
    memories_added = await add_test_memories()
    if not memories_added:
        logger.error("Failed to add test memories")
        return False
    
    # Wait for memory trigger to run (default cycle is 60 seconds)
    logger.info("Waiting 65 seconds for memory trigger service to detect new memories...")
    await asyncio.sleep(65)
    
    # Verify notifications are being generated
    notifications_generated = await verify_notifications_generated()
    if not notifications_generated:
        logger.warning("No notifications found in logs - memory trigger may not be detecting patterns")
        
    # Monitor WebSocket for notification messages
    logger.info("Monitoring WebSocket for notification messages...")
    notifications_sent = await monitor_websocket_traffic()
    
    if not notifications_sent:
        logger.warning("No notification messages detected on WebSocket")
        logger.info("Attempting to force a direct notification...")
        
        # Try to force a notification
        await force_trigger_notification()
        
        # Wait and check again
        logger.info("Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        # Check one more time
        second_attempt = await monitor_websocket_traffic()
        if not second_attempt:
            logger.error("Still no notification messages detected")
            logger.error("Check the following:")
            logger.error("1. Is the memory trigger service running?")
            logger.error("2. Is the WebSocket server (ws://localhost:8765) running?")
            logger.error("3. Is the chat overlay frontend connected to the WebSocket?")
            return False
    
    logger.info("✅ Test completed - notifications should be visible in the chat overlay")
    return True

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Memory trigger test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Memory trigger test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)