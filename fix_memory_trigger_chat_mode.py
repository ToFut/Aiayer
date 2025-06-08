#!/usr/bin/env python3
"""
Fix Memory Trigger ChatMode Issue

This script patches the memory_trigger_service.py file to add the missing ChatMode enum
and fix the notification display issues.
"""

import os
import sys
import re
import logging
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger_fix")

# Define the ChatMode enum class that will be added
class ChatMode(Enum):
    """Chat mode enum to match what's used in the brain router"""
    ASK = "ASK"
    SUGGEST = "SUGGEST"
    AGENT = "AGENT"
    GENERAL = "GENERAL"

# Path to memory_trigger_service.py
MEMORY_TRIGGER_PATH = "memory/memory_trigger_service.py"

def apply_fix():
    """Apply the ChatMode enum fix to memory_trigger_service.py"""
    try:
        # Check if file exists
        if not os.path.exists(MEMORY_TRIGGER_PATH):
            logger.error(f"File not found: {MEMORY_TRIGGER_PATH}")
            return False
        
        # Read file content
        with open(MEMORY_TRIGGER_PATH, 'r') as f:
            content = f.read()
        
        # Check if ChatMode is already defined
        if "class ChatMode(Enum)" in content:
            logger.info("ChatMode enum is already defined. No fix needed.")
            return True
        
        # Find import section to add ChatMode enum
        import_section_end = re.search(r"import.*?\n\n", content, re.DOTALL)
        if not import_section_end:
            logger.error("Could not find import section in the file")
            return False
        
        # Define ChatMode enum code to insert
        chat_mode_code = """
# Chat mode enum for brain router compatibility
class ChatMode(Enum):
    \"\"\"Chat mode enum to match what's used in the brain router\"\"\"
    ASK = "ASK"
    SUGGEST = "SUGGEST"
    AGENT = "AGENT"
    GENERAL = "GENERAL"

"""
        
        # Insert ChatMode enum after import section
        insert_position = import_section_end.end()
        new_content = content[:insert_position] + chat_mode_code + content[insert_position:]
        
        # Fix error in _push_notification_to_chat method
        # This is to ensure the notification gets delivered even if there's an error 
        # in the brain router process_request call
        push_notification_pattern = r"async def _push_notification_to_chat\(.*?\):"
        push_notification_match = re.search(push_notification_pattern, new_content, re.DOTALL)
        
        if push_notification_match:
            method_start = push_notification_match.start()
            # Find the end of the method
            method_block = new_content[method_start:]
            indentation = re.search(r"^\s+", method_block.split("\n")[1]).group() if "\n" in method_block else "    "
            
            # Find line with self.brain_router.process_request(request)
            process_request_pattern = r"response = await self\.brain_router\.process_request\(request\)"
            process_request_match = re.search(process_request_pattern, method_block)
            
            if process_request_match:
                # Add try-except block around the process_request call
                old_line = process_request_pattern
                new_code = f"""try:
{indentation}    # Send notification
{indentation}    logger.info(f"Sending notification to chat interface in direct format: {{notification.title}}")
{indentation}    response = await self.brain_router.process_request(request)
{indentation}    
{indentation}    if response.success:
{indentation}        logger.info(f"✅ Successfully pushed notification {{notification.id}} to chat")
{indentation}        # Update notification status to delivered
{indentation}        self.notification_manager.mark_notification_delivered(notification.id)
{indentation}except Exception as e:
{indentation}    logger.error(f"Error pushing notification to chat: {{e}}")
{indentation}    # Try fallback format if direct format fails
{indentation}    try:
{indentation}        # Create fallback format - simpler message
{indentation}        fallback_message = {{
{indentation}            "type": "chat_message",
{indentation}            "mode": "SUGGEST",
{indentation}            "message": f"💡 {{notification.title}}: {{notification.description or notification.suggestion}}",
{indentation}            "user_id": "system",
{indentation}            "session_id": f"suggestion_{{notification.id}}",
{indentation}            "timestamp": time.time(),
{indentation}            "suggestion_type": "memory_trigger"
{indentation}        }}
{indentation}        
{indentation}        await self.brain_router.process_request(
{indentation}            type('MockRequest', (), {{
{indentation}                'mode': "SUGGEST",
{indentation}                'query': notification.title,
{indentation}                'user_id': "system",
{indentation}                'session_id': f"fallback_{{notification.id}}",
{indentation}                'timestamp': time.time(),
{indentation}                'context': {{"direct_message": json.dumps(fallback_message)}}
{indentation}            }})
{indentation}        )
{indentation}        logger.info(f"✅ Successfully pushed notification via fallback format")
{indentation}        self.notification_manager.mark_notification_delivered(notification.id)
{indentation}    except Exception as inner_e:
{indentation}        logger.error(f"Error with fallback notification format: {{inner_e}}")
{indentation}        import traceback
{indentation}        logger.error(traceback.format_exc())"""
                
                # Find the block of code to replace
                block_pattern = r"logger\.info.*?mark_notification_delivered.*?\)"
                block_match = re.search(block_pattern, method_block, re.DOTALL)
                
                if block_match:
                    old_block = method_block[block_match.start():block_match.end()]
                    new_method_block = method_block.replace(old_block, new_code)
                    new_content = new_content[:method_start] + new_method_block
                else:
                    logger.warning("Could not find notification delivery block to enhance with fallback")
            else:
                logger.warning("Could not find process_request call in _push_notification_to_chat method")
        else:
            logger.warning("Could not find _push_notification_to_chat method")
        
        # Write updated content back to file
        with open(MEMORY_TRIGGER_PATH, 'w') as f:
            f.write(new_content)
        
        logger.info(f"✅ Successfully applied ChatMode enum fix to {MEMORY_TRIGGER_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_test_notification_script():
    """Create a script to test direct notification sending"""
    test_script_path = "send_direct_suggestion.py"
    
    if os.path.exists(test_script_path):
        logger.info(f"Test script already exists: {test_script_path}")
        return True
    
    try:
        test_script_content = """#!/usr/bin/env python3
\"\"\"
Direct Suggestion Sender - Test Tool

This script sends a direct suggestion to the WebSocket server on port 8765
to test the notification display in the chat overlay.
\"\"\"

import asyncio
import websockets
import json
import logging
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("send_suggestion")

# WebSocket server URI
WS_URI = "ws://localhost:8765"

async def send_suggestion():
    \"\"\"Send a test suggestion to the WebSocket server\"\"\"
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        # Connect to WebSocket server
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            logger.info(f"Received welcome message: {welcome[:100]}...")
            
            # Create shopping suggestion
            suggestion = {
                "type": "do_button",
                "action": "display",
                "content": {
                    "title": "Shopping Suggestion",
                    "message": "I noticed you're looking at products. Would you like me to help you find the best deals?",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, help me",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ],
                    "context": {
                        "type": "shopping",
                        "keywords": ["product", "price", "deal"]
                    }
                }
            }
            
            # Send suggestion
            await ws.send(json.dumps(suggestion))
            logger.info("✅ Sent shopping suggestion to WebSocket server")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Chat message format
            chat_message = {
                "type": "chat_message",
                "mode": "SUGGEST",
                "message": "💡 I noticed you're shopping. Can I help find the best deals?",
                "user_id": "system",
                "session_id": f"test_suggestion_{int(time.time())}",
                "timestamp": time.time(),
                "suggest_buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "type": "secondary"
                    }
                ],
                "context": {
                    "type": "shopping",
                    "keywords": ["product", "price", "deal"]
                }
            }
            
            # Send chat message format
            await ws.send(json.dumps(chat_message))
            logger.info("✅ Sent chat message suggestion to WebSocket server")
            
            # Wait a moment for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
            
            return True
            
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    \"\"\"Main function\"\"\"
    result = await send_suggestion()
    if result:
        logger.info("✅ Successfully sent test suggestion")
        print("✅ Test suggestion sent successfully!")
        print("Check the chat overlay to see if the suggestion appears.")
    else:
        logger.error("❌ Failed to send test suggestion")
        print("❌ Failed to send test suggestion.")
        print("Make sure the WebSocket server is running on port 8765.")
        print("You can start it with: python overlay/minimal_ws_server.py")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
"""
        
        with open(test_script_path, 'w') as f:
            f.write(test_script_content)
        
        # Make it executable
        os.chmod(test_script_path, 0o755)
        
        logger.info(f"✅ Created test script: {test_script_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test script: {e}")
        return False

def update_connector_script():
    """Update the connect_memory_trigger.py script with better error handling"""
    connector_path = "connect_memory_trigger.py"
    
    if not os.path.exists(connector_path):
        logger.warning(f"Connector script not found: {connector_path}")
        return False
    
    try:
        # Read current content
        with open(connector_path, 'r') as f:
            content = f.read()
        
        # Check if the script already has the fix
        if "# Import ChatMode from memory_trigger_service" in content:
            logger.info("Connector script already updated with ChatMode fix")
            return True
        
        # Add ChatMode import fix
        import_pattern = r"from memory\.memory_trigger_service import MemoryTriggerService"
        import_replacement = r"from memory.memory_trigger_service import MemoryTriggerService, ChatMode"
        
        # Apply fix
        if re.search(import_pattern, content):
            content = re.sub(import_pattern, import_replacement, content)
            
            # Add fallback for ChatMode import
            process_request_method_pattern = r"async def process_request\(self, request\):"
            process_request_method_match = re.search(process_request_method_pattern, content)
            
            if process_request_method_match:
                method_start = process_request_method_match.start()
                method_content = content[method_start:]
                indentation = re.search(r"^\s+", method_content.split("\n")[1]).group() if "\n" in method_content else "    "
                
                # Add ChatMode fallback at the beginning of the method
                mode_check = f"""# Check if ChatMode is available, or use string
{indentation}mode = request.mode
{indentation}if hasattr(request, 'mode') and not isinstance(request.mode, str):
{indentation}    # Already using proper ChatMode enum
{indentation}    pass
{indentation}elif hasattr(request, 'mode'):
{indentation}    # Convert string to enum
{indentation}    try:
{indentation}        mode = ChatMode(request.mode) if hasattr(ChatMode, request.mode) else request.mode
{indentation}    except (ValueError, AttributeError):
{indentation}        # Fallback to string
{indentation}        mode = request.mode
"""
                
                # Insert fallback after the try line
                try_pattern = r"{0}try:".format(indentation)
                try_match = re.search(try_pattern, method_content)
                
                if try_match:
                    end_of_try_line = method_start + try_match.end()
                    content = content[:end_of_try_line] + "\n" + mode_check + content[end_of_try_line:]
            
            # Write updated content back to file
            with open(connector_path, 'w') as f:
                f.write(content)
            
            logger.info(f"✅ Updated connector script with ChatMode fix: {connector_path}")
            return True
        else:
            logger.warning(f"Could not find import pattern in connector script")
            return False
        
    except Exception as e:
        logger.error(f"Error updating connector script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    # Create "memory" directory if it doesn't exist
    os.makedirs("memory", exist_ok=True)
    
    print("🔧 Fixing Memory Trigger ChatMode Issue")
    print("======================================")
    
    # Apply ChatMode enum fix
    print("1️⃣ Applying ChatMode enum fix to memory_trigger_service.py...")
    if apply_fix():
        print("✅ ChatMode enum fix applied successfully")
    else:
        print("❌ Failed to apply ChatMode enum fix")
    
    # Create test notification script
    print("\n2️⃣ Creating test notification script...")
    if create_test_notification_script():
        print("✅ Test script created: send_direct_suggestion.py")
    else:
        print("❌ Failed to create test script")
    
    # Update connector script
    print("\n3️⃣ Updating connector script...")
    if update_connector_script():
        print("✅ Connector script updated successfully")
    else:
        print("❌ Failed to update connector script")
    
    print("\n📋 Next Steps:")
    print("1. Start the WebSocket server:")
    print("   python overlay/minimal_ws_server.py")
    print("2. Test direct notification sending:")
    print("   python send_direct_suggestion.py")
    print("3. Start the memory trigger connector:")
    print("   python connect_memory_trigger.py")
    print("4. Add test memories to generate notifications:")
    print("   python add_test_memory.py shopping")
    print("\nThe memory trigger system should now correctly display notifications in the chat interface.")

if __name__ == "__main__":
    main()