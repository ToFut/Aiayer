#!/usr/bin/env python3
"""
Fix WebSocket Agent Response Handling
This script patches the enhanced_enterprise_backend_with_context.py file to properly handle agent mode responses.
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
    
    # Find the handle_chat_request_streaming method
    if "async def handle_chat_request_streaming" not in content:
        print("Error: Could not find handle_chat_request_streaming method!")
        return False
    
    # Check if the fixed_handle_universal_automation function is already being called
    if "fixed_handle_universal_automation" in content and "plan_id" in content:
        print("✅ Fixed universal automation handler already integrated")
    else:
        print("⚠️ Universal automation handler needs to be updated")
    
    # Check if the response includes streaming of automation plans
    if "type': 'agent_automation_plan'" in content and "await websocket.send(json.dumps(automation_plan_msg))" in content:
        print("✅ Automation plan streaming already implemented")
    else:
        print("⚠️ Automation plan streaming needs to be added")
    
    # Fix 1: Ensure automation plan results are properly sent back
    if "return await self.handle_agent_mode(message, session_id)" in content and "automation_result =" not in content:
        print("🔧 Fixing agent mode automation result handling...")
        
        # Pattern to find the agent mode handling code
        pattern = r"(if\s+mode\.lower\(\)\s*==\s*['\"]agent['\"]\s*.*?return await self\.handle_agent_mode\(message, session_id\))"
        
        # Replacement with proper response handling
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
                return f"I encountered an error while planning automation: {str(e)}"
        
        # Apply the fix
        modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if modified_content != content:
            # Write the fixed content
            with open(backend_file, "w") as f:
                f.write(modified_content)
            print("✅ Fixed agent mode response handling")
            return True
        else:
            print("⚠️ Could not apply agent mode response handling fix")
            return False
    else:
        print("✅ Agent mode response handling already fixed")
        return True

if __name__ == "__main__":
    print("🔧 Fixing WebSocket Agent Response Handling...")
    success = fix_websocket_agent_response()
    
    if success:
        print("✅ Fix applied successfully!")
        print("🔄 Restart the system with ./RESTART_FIXED_SYSTEM.sh to apply changes")
    else:
        print("❌ Fix application failed!")
        print("Try manual fix of enhanced_enterprise_backend_with_context.py")
    