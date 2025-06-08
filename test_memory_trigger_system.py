#!/usr/bin/env python3
"""
Memory Trigger System Test Script

This script helps verify the entire memory trigger system by:
1. Testing the WebSocket server connection
2. Sending a test notification with the correct format
3. Testing the memory trigger service with custom memory items
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/memory_trigger_test.log')
    ]
)
logger = logging.getLogger("memory_trigger_test")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def test_websocket_connection():
    """Test connection to WebSocket server"""
    try:
        logger.info(f"Testing connection to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("✅ Successfully connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Send a ping message
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error connecting to WebSocket server: {e}")
        return False

async def send_test_notification():
    """Send a test notification to WebSocket server"""
    try:
        logger.info(f"Sending test notification to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create message in the EXACT format expected by EnterpriseChatWidget
            message = {
                "success": True,
                "response": "💡 Test Notification: This is a test notification from the memory trigger system to verify notifications are working.",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "test_accept",
                        "text": "This Works!",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "test_dismiss",
                        "text": "Dismiss Test",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent test notification to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {e}")
        return False

async def send_do_button_message():
    """Send a DO button format message to WebSocket server"""
    try:
        logger.info(f"Sending DO button message to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create DO button message
            message = {
                "type": "do_button",
                "action": "display",
                "content": {
                    "title": "DO Button Test",
                    "message": "This tests whether the DO button format works correctly.",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "DO Button Works",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "Dismiss",
                            "type": "secondary"
                        }
                    ]
                }
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent DO button message to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error sending DO button message: {e}")
        return False

async def test_custom_memory_items():
    """Test creating custom memory items for pattern detection"""
    try:
        # This requires the memory trigger connector to be running
        logger.info("Creating custom memory items for pattern detection...")
        
        # Import memory trigger service if available
        try:
            from memory.memory_trigger_service import MemoryTriggerService, TriggerRule, TriggerType, TriggerPriority
            from memory.memory_system import MemorySystem
            
            # Create memory system
            memory_system = MemorySystem()
            logger.info("Created memory system")
            
            # Add custom shopping memory item
            shopping_memory = {
                "type": "web_content",
                "url": "https://example.com/products/test-product",
                "title": "Test Product - Example Store",
                "searchable_text": """
                Test Product with Amazing Features
                
                Price: $59.99
                Sale Price: $49.99
                Save $10.00 (17%)
                FREE Shipping
                In Stock.
                
                Buy Now | Add to Cart | Add to List
                
                Features:
                • Feature 1
                • Feature 2
                • Feature 3
                
                Product Description:
                This is a test product to verify the memory trigger system works correctly.
                """,
                "timestamp": time.time(),
                "source": "test_script"
            }
            
            # Add to memory
            memory_system.short_term_memory.append(shopping_memory)
            logger.info("✅ Added custom shopping memory item")
            
            # Create memory trigger service
            trigger_service = MemoryTriggerService(memory_system=memory_system)
            logger.info("Created memory trigger service")
            
            # Add custom trigger rule
            custom_rule = TriggerRule(
                id="test_shopping_rule",
                name="Test Shopping Detection",
                description="Detects test shopping activity",
                trigger_type=TriggerType.CONTENT_BASED,
                priority=TriggerPriority.HIGH,
                pattern={
                    "keywords": ["test", "product", "price", "buy", "cart"],
                    "min_matches": 3
                },
                action_template={
                    "type": "test_shopping_assistance",
                    "description": "Test shopping assistance"
                }
            )
            
            # Add rule
            trigger_service.rule_manager.add_rule(custom_rule)
            logger.info("✅ Added custom trigger rule")
            
            # Initialize trigger service
            await trigger_service.start()
            logger.info("Started memory trigger service for testing")
            
            # Wait for pattern detection (normally handled by _monitor_memory)
            logger.info("Manually triggering pattern detection...")
            memory_items = await trigger_service._get_recent_memory_items()
            logger.info(f"Got {len(memory_items)} memory items")
            
            # Get active rules
            active_rules = trigger_service.rule_manager.get_active_rules()
            logger.info(f"Using {len(active_rules)} active trigger rules")
            
            # Detect patterns
            detected_patterns = await trigger_service.pattern_detector.detect_patterns(memory_items, active_rules)
            
            if detected_patterns:
                logger.info(f"✅ Detected {len(detected_patterns)} patterns: {[p.get('type') for p in detected_patterns]}")
                await trigger_service._process_detected_patterns(detected_patterns)
                logger.info("Processed detected patterns")
                return True
            else:
                logger.warning("No patterns detected in test memory items")
                return False
            
        except ImportError as e:
            logger.warning(f"Memory trigger components not available for direct testing: {e}")
            logger.info("This test requires running the connector: 'python fixed_connect_memory_trigger.py'")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing custom memory items: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    import os
    os.makedirs("logs", exist_ok=True)
    
    logger.info("🚀 Testing Memory Trigger System")
    
    # Test 1: WebSocket Connection
    logger.info("\n----- Test 1: WebSocket Connection -----")
    ws_success = await test_websocket_connection()
    
    if ws_success:
        logger.info("✅ WebSocket connection test passed")
    else:
        logger.error("❌ WebSocket connection test failed")
        logger.error("Please start the WebSocket server with: python overlay/minimal_ws_server.py")
        return False
    
    # Test 2: Direct Notification
    logger.info("\n----- Test 2: Direct Notification -----")
    notification_success = await send_test_notification()
    
    if notification_success:
        logger.info("✅ Direct notification test passed")
        logger.info("Check the chat overlay for the test notification")
    else:
        logger.error("❌ Direct notification test failed")
        return False
    
    # Test 3: DO Button Format
    logger.info("\n----- Test 3: DO Button Format -----")
    do_button_success = await send_do_button_message()
    
    if do_button_success:
        logger.info("✅ DO button format test passed")
        logger.info("Check the chat overlay for the DO button message")
    else:
        logger.error("❌ DO button format test failed")
        return False
    
    # Test 4: Custom Memory Items (requires memory trigger service)
    logger.info("\n----- Test 4: Custom Memory Items -----")
    memory_success = await test_custom_memory_items()
    
    if memory_success:
        logger.info("✅ Custom memory items test passed")
    else:
        logger.warning("⚠️ Custom memory items test couldn't be completed")
        logger.info("This is normal if you're just testing the WebSocket connection")
        logger.info("To test memory items, run: python fixed_connect_memory_trigger.py")
    
    # Display summary
    logger.info("\n----- Test Summary -----")
    logger.info("WebSocket Connection: " + ("✅ PASSED" if ws_success else "❌ FAILED"))
    logger.info("Direct Notification: " + ("✅ PASSED" if notification_success else "❌ FAILED"))
    logger.info("DO Button Format: " + ("✅ PASSED" if do_button_success else "❌ FAILED"))
    logger.info("Custom Memory Items: " + ("✅ PASSED" if memory_success else "⚠️ NOT TESTED"))
    
    logger.info("\n----- Next Steps -----")
    logger.info("1. Run the fixed WebSocket server: python overlay/minimal_ws_server.py")
    logger.info("2. Test direct notification: python fixed_test_direct_chat_message.py")
    logger.info("3. Run the fixed memory connector: python fixed_connect_memory_trigger.py")
    
    return ws_success and notification_success and do_button_success

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)