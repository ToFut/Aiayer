#!/usr/bin/env python3
"""
Direct Fix for WebSocket Agent Response Handling
This script directly patches the enhanced_enterprise_backend_with_context.py file
to properly handle agent mode responses.
"""

import re
import os
import sys

def fix_websocket_agent_response():
    """Fix WebSocket agent mode response handling"""
    
    # Path to the backend file
    backend_file = "enhanced_enterprise_backend_with_context.py"
    
    if not os.path.exists(backend_file):
        print(f"Error: {backend_file} not found!")
        return False
    
    # Read the file content
    with open(backend_file, "r") as f:
        content = f.read()
    
    # Find the handle_contextual_chat_request_streaming method
    if "async def handle_contextual_chat_request_streaming" not in content:
        print("Error: Could not find handle_contextual_chat_request_streaming method!")
        return False
    
    # Check if we need to modify the agent mode handling
    need_to_modify = False
    
    # Look for simple return without error handling
    if "if mode.lower() == 'agent':" in content and "return await self.handle_agent_mode(message, session_id)" in content:
        if "try:" not in content[content.find("if mode.lower() == 'agent':"):content.find("return await self.handle_agent_mode(message, session_id)") + 60]:
            need_to_modify = True
    
    if not need_to_modify:
        print("✅ Agent mode response handling already fixed")
        return True
    
    print("🔧 Fixing agent mode automation result handling...")
    
    # Find the part that needs to be replaced - looking for the if mode.lower() == 'agent' block
    # that directly returns self.handle_agent_mode without proper error handling
    
    start_pattern = r"if\s+mode\.lower\(\)\s*==\s*['\"]agent['\"]\s*:"
    end_pattern = r"return await self\.handle_agent_mode\(message, session_id\)"
    
    match = re.search(start_pattern, content)
    if not match:
        print("⚠️ Could not find agent mode handling block")
        return False
    
    start_pos = match.start()
    
    match = re.search(end_pattern, content)
    if not match:
        print("⚠️ Could not find agent mode return statement")
        return False
    
    end_pos = match.end()
    
    # Check if these positions look valid
    if end_pos < start_pos or end_pos - start_pos > 1000:  # Sanity check
        print("⚠️ Invalid code positions found")
        return False
    
    # Extract the section to replace
    section_to_replace = content[start_pos:end_pos]
    print(f"Found code to replace: {section_to_replace[:50]}...")
    
    # Create replacement code
    replacement = """if mode.lower() == 'agent':
            try:
                # Use fixed_handle_universal_automation for better plan handling
                if "search" in message.lower() or "google" in message.lower() or "safari" in message.lower():
                    try:
                        from fixed_universal_automation_handler import fixed_handle_universal_automation
                        automation_result = await fixed_handle_universal_automation(message, session_id)
                        
                        # Send automation plan to client
                        if automation_result.get("plan_id"):
                            automation_plan_msg = {
                                'type': 'agent_automation_plan',
                                'plan': {
                                    'plan_id': automation_result.get("plan_id"),
                                    'steps': automation_result.get("buttons", []),
                                    'task': message
                                },
                                'timestamp': time.time()
                            }
                            await websocket.send(json.dumps(automation_plan_msg))
                            
                        # Return the formatted response
                        return automation_result.get("response", "No response from automation handler")
                    except Exception as e:
                        self.logger.error(f"Error using fixed automation handler: {e}")
                        # Fall back to standard handler
                
                # Standard agent mode handling
                return await self.handle_agent_mode(message, session_id)
            except Exception as e:
                self.logger.error(f"❌ Error in Agent mode automation: {e}")
                return f"I encountered an error while planning automation: {str(e)}\""""
    
    # Replace the section in the content
    modified_content = content.replace(section_to_replace, replacement)
    
    if modified_content == content:
        print("⚠️ No changes were made to the file")
        return False
    
    # Write the modified content back
    with open(backend_file, "w") as f:
        f.write(modified_content)
    
    print("✅ Fixed agent mode response handling")
    return True

if __name__ == "__main__":
    print("🔧 Fixing WebSocket Agent Response Handling...")
    success = fix_websocket_agent_response()
    
    if success:
        print("✅ Fix applied successfully!")
        print("🔄 Restart the system with ./RESTART_FIXED_SYSTEM.sh to apply changes")
    else:
        print("❌ Fix application failed!")
        print("Try manually updating enhanced_enterprise_backend_with_context.py")