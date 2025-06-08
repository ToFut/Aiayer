#!/usr/bin/env python3
"""
Fix the START_MASTER_SYSTEM.sh script by addressing syntax errors with sed commands
"""
import os
import sys
import re
import shutil
from datetime import datetime

def main():
    print("🔧 Fixing START_MASTER_SYSTEM.sh script...")
    
    # Backup the original script
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    script_path = "START_MASTER_SYSTEM.sh"
    backup_path = f"START_MASTER_SYSTEM.sh.bak.{timestamp}"
    
    # Create backup
    shutil.copy2(script_path, backup_path)
    print(f"✅ Created backup at {backup_path}")
    
    # Read the original script
    with open(script_path, 'r') as file:
        content = file.read()
    
    # Fix sed commands with proper escaping and quotes
    # Instead of trying to escape complex sed commands, we'll use a simpler approach
    # by creating temporary files for each replacement

    # Write the fixed methods to temporary files
    ollama_method = '''    def check_ollama_availability(self) -> bool:
        """Check if Ollama is available on the system"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
            '''
    
    with open('ollama_method.txt', 'w') as f:
        f.write(ollama_method)
    
    deep_data_method = '''    async def _try_agnostic_deep_data_access(self, message: str, mode: str, client_id: str, websocket) -> Dict[str, Any]:
        """Try to handle universal agnostic deep data access for any query"""
        return {"handled": False}  # Default to not handled
            '''
    
    with open('deep_data_method.txt', 'w') as f:
        f.write(deep_data_method)
    
    fallback_response = '''            # Provide a fallback response
            response = f"I understand your message about '{message}'. How can I assist you further?"
            await websocket.send(json.dumps({
                "type": "chat_response",
                "mode": mode,
                "response": response,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }))'''
    
    with open('fallback_response.txt', 'w') as f:
        f.write(fallback_response)
    
    # Replace the complex sed commands with simpler ones that use these files
    content = content.replace(
        '''    sed -i.ollama.bak '/async def _initialize_contextual_knowledge/i \\
    def check_ollama_availability(self) -> bool:\\
        """Check if Ollama is available on the system"""\\
        try:\\
            import requests\\
            response = requests.get("http://localhost:11434/api/tags", timeout=1)\\
            return response.status_code == 200\\
        except Exception as e:\\
            logger.warning(f"Ollama not available: {e}")\\
            return False\\
            ' enhanced_enterprise_backend_with_context.py 2>/dev/null || true''',
        
        '''    sed -i.ollama.bak "/async def _initialize_contextual_knowledge/i $(cat ollama_method.txt)" enhanced_enterprise_backend_with_context.py 2>/dev/null || true'''
    )
    
    content = content.replace(
        '''    sed -i.deep.bak '/async def handle_contextual_chat_request_streaming/i \\
    async def _try_agnostic_deep_data_access(self, message: str, mode: str, client_id: str, websocket) -> Dict[str, Any]:\\
        """Try to handle universal agnostic deep data access for any query"""\\
        return {"handled": False}  # Default to not handled\\
            ' enhanced_enterprise_backend_with_context.py 2>/dev/null || true''',
        
        '''    sed -i.deep.bak "/async def handle_contextual_chat_request_streaming/i $(cat deep_data_method.txt)" enhanced_enterprise_backend_with_context.py 2>/dev/null || true'''
    )
    
    content = content.replace(
        '''    sed -i.fallback.bak '/# Continue with other chat modes processing here/a \\
            # Provide a fallback response\\
            response = f"I understand your message about \'{message}\'. How can I assist you further?"\\
            await websocket.send(json.dumps({\\
                "type": "chat_response",\\
                "mode": mode,\\
                "response": response,\\
                "client_id": client_id,\\
                "timestamp": datetime.now().isoformat(),\\
                "fallback": True\\
            }))' enhanced_enterprise_backend_with_context.py 2>/dev/null || true''',
        
        '''    sed -i.fallback.bak "/# Continue with other chat modes processing here/a $(cat fallback_response.txt)" enhanced_enterprise_backend_with_context.py 2>/dev/null || true'''
    )
    
    # Write the fixed content back to the file
    with open(script_path, 'w') as file:
        file.write(content)
    
    print(f"✅ Fixed START_MASTER_SYSTEM.sh script")
    
    # Make it executable
    os.chmod(script_path, 0o755)
    print(f"✅ Made script executable")
    
    print("🚀 Done! You can now run ./START_MASTER_SYSTEM.sh")

if __name__ == "__main__":
    main()