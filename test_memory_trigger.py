"""
Test script for memory trigger service
This script adds test memory items and verifies that notifications are generated.
"""

import asyncio
import time
import logging
import json
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_memory_trigger")

# Try to import memory components
try:
    from memory.memory_system import MemorySystem
    from memory.memory_trigger_service import MemoryTriggerService, TriggerRule, TriggerType, TriggerPriority
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

async def add_test_web_memory(memory_system):
    """Add test web content to memory"""
    logger.info("Adding test web content to memory")
    
    # Add web page memory item
    web_memory = {
        "type": "web_content",
        "url": "https://example.com/test-article",
        "title": "Test Article About Python Programming",
        "searchable_text": """
        Python Tutorial: Learning Python Programming
        
        This comprehensive tutorial introduces Python programming for beginners.
        Python is a versatile language used for web development, data analysis,
        artificial intelligence, and automation.
        
        Key Python Features:
        - Easy to learn and read
        - Extensive libraries and frameworks
        - Cross-platform compatibility
        - Large community support
        
        Python is widely used in data science, machine learning, web development,
        and many other fields. Learning Python opens many career opportunities.
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(web_memory)
    logger.info("Added web content memory")
    
    # Add application memory
    app_memory = {
        "type": "application",
        "application": "Google Chrome",
        "title": "Python Tutorial - Google Chrome",
        "searchable_text": "Browser window showing Python programming tutorial",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(app_memory)
    logger.info("Added application memory")
    
    return True

async def create_test_trigger_rules():
    """Create test trigger rules"""
    rules = []
    
    # Web content rule
    web_rule = TriggerRule(
        id="web_content_rule",
        name="Web Content Detection",
        description="Detects when user is viewing web content",
        trigger_type=TriggerType.CONTENT_BASED,
        priority=TriggerPriority.MEDIUM,
        pattern={"keywords": ["tutorial", "article", "guide"]},
        confidence_threshold=0.6,
        cooldown_seconds=60,
        action_template={
            "type": "web_content_action",
            "suggestion": "I can help you understand this content better."
        }
    )
    rules.append(web_rule)
    
    # Application rule
    app_rule = TriggerRule(
        id="application_rule",
        name="Application Detection",
        description="Detects when user is using specific applications",
        trigger_type=TriggerType.APPLICATION_PATTERN,
        priority=TriggerPriority.MEDIUM,
        pattern={"applications": ["Chrome", "Firefox", "Safari"]},
        confidence_threshold=0.7,
        cooldown_seconds=60,
        action_template={
            "type": "application_assistance",
            "suggestion": "I can help you with this application."
        }
    )
    rules.append(app_rule)
    
    return rules

class SimpleNotificationCallback:
    """Simple callback to verify notifications are created"""
    
    def __init__(self):
        self.notifications = []
        
    def __call__(self, notification):
        logger.info(f"🔔 NOTIFICATION RECEIVED: {notification.title}")
        logger.info(f"  Description: {notification.description}")
        logger.info(f"  Suggestion: {notification.suggestion}")
        logger.info(f"  Priority: {notification.priority.value}")
        logger.info(f"  Status: {notification.status.value}")
        self.notifications.append(notification)

class MockBrainRouter:
    """Mock brain router for testing"""
    
    async def process_request(self, request):
        logger.info(f"💬 CHAT REQUEST: {request.mode} - {request.query}")
        # Log notification context
        if hasattr(request, 'context') and request.context:
            logger.info(f"  Context: {json.dumps(request.context, default=str)}")
        
        # Return mock response
        return type('MockResponse', (), {
            'success': True,
            'response': "This is a mock response"
        })

async def main():
    """Main test function"""
    if not IMPORTS_AVAILABLE:
        logger.error("Required imports not available. Cannot run test.")
        return False
    
    try:
        logger.info("🚀 Starting memory trigger service test")
        
        # Create memory system
        memory_system = MemorySystem()
        logger.info("Created memory system")
        
        # Create mock brain router
        brain_router = MockBrainRouter()
        logger.info("Created mock brain router")
        
        # Create trigger rules
        rules = await create_test_trigger_rules()
        logger.info(f"Created {len(rules)} trigger rules")
        
        # Create memory trigger service
        trigger_service = MemoryTriggerService(
            brain_router=brain_router,
            memory_system=memory_system
        )
        
        # Set up rule manager - add rules one by one
        for rule in rules:
            trigger_service.rule_manager.add_rule(rule)
        logger.info("Added rules to trigger service")
        
        # Add notification callback
        notification_callback = SimpleNotificationCallback()
        trigger_service.notification_manager.add_notification_callback(notification_callback)
        logger.info("Added notification callback")
        
        # Start service
        await trigger_service.start()
        logger.info("Started memory trigger service")
        
        # Add test memory
        success = await add_test_web_memory(memory_system)
        if success:
            logger.info("Successfully added test memory items")
        
        # Wait for monitoring cycle
        logger.info("Waiting for monitoring cycle to detect patterns")
        # Wait longer than check_interval
        await asyncio.sleep(trigger_service.check_interval + 5)
        
        # Check for notifications
        if notification_callback.notifications:
            logger.info(f"✅ SUCCESS: Received {len(notification_callback.notifications)} notifications")
            for i, notification in enumerate(notification_callback.notifications):
                logger.info(f"  Notification {i+1}: {notification.title}")
        else:
            logger.warning("⚠️ WARNING: No notifications received")
            
        # Stop service
        await trigger_service.stop()
        logger.info("Stopped memory trigger service")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)