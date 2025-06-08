"""
Memory Trigger Integration Script

This script demonstrates how to integrate the Memory Trigger Service
with existing components to enable proactive suggestions and action execution.

Usage:
    python -m memory.integrate_memory_trigger

Example:
    # Start the integration
    python -m memory.integrate_memory_trigger --start

    # Check status
    python -m memory.integrate_memory_trigger --status

    # Add a custom rule
    python -m memory.integrate_memory_trigger --add-rule

Features:
- Connects memory trigger service to brain router and memory system
- Demonstrates how to handle notification actions
- Provides CLI for testing functionality
"""

import asyncio
import argparse
import json
import time
import sys
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_trigger_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger_integration")

# Try to import required components
try:
    from memory.memory_trigger_service import (
        memory_trigger_service, 
        initialize as init_trigger_service,
        handle_notification_action,
        get_service_status,
        add_trigger_rule,
        TriggerType,
        TriggerPriority
    )
    from brain.core.brain_router import BrainRouter
    
    # Import or create memory_system
    try:
        from memory.memory_system import memory_system
    except ImportError:
        # Create a mock memory_system or instantiate one
        try:
            from memory.memory_system import MemorySystem
            memory_system = MemorySystem()
            logger.info("Created new MemorySystem instance")
        except Exception as e:
            logger.warning(f"Failed to create memory system: {e}")
            memory_system = None
    
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import required components: {e}")
    IMPORTS_AVAILABLE = False

# Default example rule for testing
DEFAULT_TEST_RULE = {
    "id": f"test_rule_{int(time.time())}",
    "name": "Test Browser Detection",
    "description": "Detects when user is using a browser",
    "trigger_type": "application_pattern",
    "priority": "medium",
    "pattern": {"applications": ["Chrome", "Safari", "Firefox", "Edge"]},
    "confidence_threshold": 0.7,
    "action_template": {
        "type": "search_assistance",
        "description": "Help with search optimization"
    }
}

async def start_integration() -> bool:
    """Start the memory trigger integration"""
    if not IMPORTS_AVAILABLE:
        logger.error("Cannot start integration due to missing components")
        return False
    
    try:
        # Try to get BrainRouter instance if available
        brain_router = None
        try:
            from brain.core.brain_router import brain_router
        except ImportError:
            # Create a simple BrainRouter mock for testing if the real one isn't available
            logger.warning("Brain router import not available, using mock")
            brain_router = MockBrainRouter()
        
        # Initialize memory trigger service
        logger.info("Initializing memory trigger service...")
        await init_trigger_service(brain_router=brain_router, memory_system=memory_system)
        
        # Verify it's running
        status = await get_service_status()
        if status.get("running", False):
            logger.info(f"Memory trigger service started successfully: {status}")
            return True
        else:
            logger.error(f"Memory trigger service failed to start: {status}")
            return False
            
    except Exception as e:
        logger.error(f"Error starting memory trigger integration: {e}")
        return False

async def check_status() -> Dict[str, Any]:
    """Check memory trigger service status"""
    if not IMPORTS_AVAILABLE:
        return {"error": "Required components not available"}
    
    try:
        status = await get_service_status()
        logger.info(f"Memory trigger service status: {status}")
        return status
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return {"error": str(e)}

async def add_test_rule(rule_data: Optional[Dict[str, Any]] = None) -> bool:
    """Add a test rule to the memory trigger service"""
    if not IMPORTS_AVAILABLE:
        logger.error("Cannot add rule due to missing components")
        return False
    
    try:
        # Use provided rule or default
        rule = rule_data or DEFAULT_TEST_RULE
        
        # Add rule
        logger.info(f"Adding test rule: {rule['name']}")
        success = await add_trigger_rule(rule)
        
        if success:
            logger.info(f"Successfully added test rule: {rule['id']}")
        else:
            logger.error(f"Failed to add test rule")
        
        return success
    except Exception as e:
        logger.error(f"Error adding test rule: {e}")
        return False

async def test_notification_action(notification_id: str, action: str) -> Dict[str, Any]:
    """Test handling a notification action"""
    if not IMPORTS_AVAILABLE:
        return {"error": "Required components not available"}
    
    try:
        logger.info(f"Testing notification action: {action} on {notification_id}")
        result = await handle_notification_action(
            notification_id=notification_id,
            action=action,
            user_id="test_user",
            session_id="test_session"
        )
        
        logger.info(f"Action result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error testing notification action: {e}")
        return {"error": str(e)}

async def simulate_notification() -> str:
    """Simulate creating a notification for testing"""
    if not IMPORTS_AVAILABLE:
        return "Error: Required components not available"
    
    try:
        # Create a test rule
        rule_id = f"simulated_rule_{int(time.time())}"
        rule = {
            "id": rule_id,
            "name": "Simulated Rule",
            "description": "Rule created for testing",
            "trigger_type": "content_based",
            "priority": "high",
            "pattern": {"keywords": ["test", "simulate", "notification"]},
            "action_template": {
                "type": "test_action",
                "description": "Simulated test action"
            }
        }
        
        # Add the rule
        await add_trigger_rule(rule)
        
        # Directly create a notification using the service's internals
        pattern = {
            "type": "content_based",
            "confidence": 0.9,
            "context": {
                "matched_keywords": ["test", "simulate"],
                "content_type": "test"
            },
            "description": "Simulated pattern match for testing"
        }
        
        # Get rule object
        trigger_rule = memory_trigger_service.rule_manager.get_rule(rule_id)
        if not trigger_rule:
            return "Error: Failed to retrieve rule"
        
        # Create notification
        notification = memory_trigger_service.notification_manager.create_notification(
            trigger_rule, pattern
        )
        
        # Generate a suggestion
        suggestion = await memory_trigger_service._generate_suggestion(notification, trigger_rule)
        
        # Update notification with suggestion
        memory_trigger_service.notification_manager.update_notification(
            notification.id,
            {"suggestion": suggestion}
        )
        
        logger.info(f"Created simulated notification: {notification.id}")
        return notification.id
    except Exception as e:
        logger.error(f"Error simulating notification: {e}")
        return f"Error: {str(e)}"

def create_interactive_rule() -> Dict[str, Any]:
    """Create a rule interactively via CLI"""
    try:
        print("\n===== Create Custom Trigger Rule =====")
        
        # Basic rule info
        rule_id = input("Rule ID (leave blank for auto-generated): ").strip()
        if not rule_id:
            rule_id = f"custom_rule_{int(time.time())}"
        
        name = input("Rule name: ").strip()
        if not name:
            name = "Custom Rule"
        
        description = input("Rule description: ").strip()
        if not description:
            description = "Custom trigger rule"
        
        # Trigger type
        print("\nTrigger types:")
        for i, t_type in enumerate(["application_pattern", "content_based", "user_behavior", 
                                "time_based", "semantic_pattern", "task_completion"]):
            print(f"{i+1}. {t_type}")
        
        trigger_type_idx = input("Select trigger type (1-6, default=2): ").strip()
        try:
            trigger_type_idx = int(trigger_type_idx) - 1
            trigger_types = ["application_pattern", "content_based", "user_behavior", 
                            "time_based", "semantic_pattern", "task_completion"]
            trigger_type = trigger_types[trigger_type_idx]
        except:
            trigger_type = "content_based"
        
        # Priority
        print("\nPriority levels:")
        print("1. high")
        print("2. medium")
        print("3. low")
        
        priority_idx = input("Select priority (1-3, default=2): ").strip()
        try:
            priority_idx = int(priority_idx) - 1
            priorities = ["high", "medium", "low"]
            priority = priorities[priority_idx]
        except:
            priority = "medium"
        
        # Pattern (simplified for CLI)
        pattern = {}
        if trigger_type == "application_pattern":
            apps = input("Enter applications to detect (comma-separated): ").strip()
            if apps:
                pattern = {"applications": [app.strip() for app in apps.split(",")]}
            else:
                pattern = {"applications": ["Chrome", "Safari", "Firefox"]}
        elif trigger_type == "content_based":
            keywords = input("Enter keywords to detect (comma-separated): ").strip()
            if keywords:
                pattern = {"keywords": [kw.strip() for kw in keywords.split(",")], "min_matches": 1}
            else:
                pattern = {"keywords": ["research", "find", "look", "search"], "min_matches": 1}
        elif trigger_type == "time_based":
            duration = input("Enter duration in minutes (default=60): ").strip()
            try:
                duration = int(duration)
            except:
                duration = 60
            pattern = {"duration": duration}
        
        # Action template
        print("\nAction types:")
        print("1. search_assistance")
        print("2. automation_suggestion")
        print("3. code_review")
        print("4. wellness_suggestion")
        
        action_type_idx = input("Select action type (1-4, default=1): ").strip()
        try:
            action_type_idx = int(action_type_idx) - 1
            action_types = ["search_assistance", "automation_suggestion", "code_review", "wellness_suggestion"]
            action_type = action_types[action_type_idx]
        except:
            action_type = "search_assistance"
        
        action_description = input("Action description (optional): ").strip()
        if not action_description:
            action_description = f"Suggest {action_type.replace('_', ' ')}"
        
        action_template = {
            "type": action_type,
            "description": action_description
        }
        
        # Create rule dict
        rule = {
            "id": rule_id,
            "name": name,
            "description": description,
            "trigger_type": trigger_type,
            "priority": priority,
            "pattern": pattern,
            "confidence_threshold": 0.7,
            "action_template": action_template
        }
        
        print("\nCreated rule:")
        print(json.dumps(rule, indent=2))
        
        return rule
    except Exception as e:
        logger.error(f"Error in interactive rule creation: {e}")
        return DEFAULT_TEST_RULE

class MockBrainRouter:
    """Simple mock for BrainRouter for testing"""
    
    async def process_request(self, request):
        """Mock processing a request"""
        logger.info(f"Mock brain router processing request: {request.query}")
        return type('obj', (object,), {
            'success': True,
            'response': "This is a mock response from the brain router",
            'mode_used': request.mode,
            'processing_time': 0.1,
            'resources_used': ["mock"],
            'confidence': 0.9,
            'metadata': {}
        })

async def main_async():
    """Main async function"""
    parser = argparse.ArgumentParser(description="Memory Trigger Integration Tool")
    parser.add_argument("--start", action="store_true", help="Start memory trigger integration")
    parser.add_argument("--status", action="store_true", help="Check memory trigger service status")
    parser.add_argument("--add-rule", action="store_true", help="Add a test rule")
    parser.add_argument("--simulate", action="store_true", help="Simulate creating a notification")
    parser.add_argument("--action", help="Test notification action (requires --notification-id)")
    parser.add_argument("--notification-id", help="Notification ID for action testing")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if not IMPORTS_AVAILABLE:
        print("Error: Required components not available. Please make sure all dependencies are installed.")
        return 1
    
    if args.interactive:
        await interactive_mode()
        return 0
    
    if args.start:
        success = await start_integration()
        if not success:
            return 1
    
    if args.status:
        status = await check_status()
        print(json.dumps(status, indent=2))
    
    if args.add_rule:
        success = await add_test_rule()
        if not success:
            return 1
    
    if args.simulate:
        notification_id = await simulate_notification()
        print(f"Simulated notification ID: {notification_id}")
    
    if args.action and args.notification_id:
        result = await test_notification_action(args.notification_id, args.action)
        print(json.dumps(result, indent=2))
    
    if not any([args.start, args.status, args.add_rule, args.simulate, 
                (args.action and args.notification_id)]):
        parser.print_help()
    
    return 0

async def interactive_mode():
    """Run the integration in interactive mode"""
    print("\n===== Memory Trigger Integration Interactive Mode =====")
    
    while True:
        print("\nOptions:")
        print("1. Start integration")
        print("2. Check status")
        print("3. Add test rule")
        print("4. Create custom rule")
        print("5. Simulate notification")
        print("6. Test notification action")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-6): ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            print("Starting integration...")
            success = await start_integration()
            print(f"Integration started: {success}")
        
        elif choice == "2":
            print("Checking status...")
            status = await check_status()
            print(json.dumps(status, indent=2))
        
        elif choice == "3":
            print("Adding test rule...")
            success = await add_test_rule()
            print(f"Test rule added: {success}")
        
        elif choice == "4":
            print("Creating custom rule...")
            rule = create_interactive_rule()
            success = await add_trigger_rule(rule)
            print(f"Custom rule added: {success}")
        
        elif choice == "5":
            print("Simulating notification...")
            notification_id = await simulate_notification()
            print(f"Simulated notification ID: {notification_id}")
        
        elif choice == "6":
            notification_id = input("Enter notification ID: ").strip()
            print("Available actions:")
            print("1. execute")
            print("2. dismiss")
            action_choice = input("Select action (1-2): ").strip()
            
            if action_choice == "1":
                action = "execute"
            elif action_choice == "2":
                action = "dismiss"
            else:
                print("Invalid choice, using 'execute'")
                action = "execute"
            
            print(f"Testing action '{action}' on notification '{notification_id}'...")
            result = await test_notification_action(notification_id, action)
            print(json.dumps(result, indent=2))
        
        else:
            print("Invalid choice, please try again.")

def main():
    """Main entry point"""
    return asyncio.run(main_async())

if __name__ == "__main__":
    sys.exit(main())