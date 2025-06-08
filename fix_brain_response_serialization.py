#!/usr/bin/env python3
"""
Fix BrainResponse Serialization Issue

This script fixes how BrainResponse objects are serialized before being sent
to the overlay. Instead of using the string representation, it properly
converts them to JSON objects that can be easily handled by the frontend.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/brain_response_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_backend_files():
    """Fix backend files to properly handle BrainResponse objects"""
    
    # List of files to fix
    files_to_fix = [
        "enhanced_enterprise_backend_with_context.py",
        "enhanced_brain_router_with_full_automation.py"
    ]
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
        
        logger.info(f"Fixing {file_path}...")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Fix 1: Make BrainResponse JSON serializable
            if "def to_dict" not in content and "class BrainResponse" in content:
                # Add to_dict method to BrainResponse class
                fixed_content = content.replace(
                    "class BrainResponse:",
                    """class BrainResponse:
    def to_dict(self):
        """Convert BrainResponse to a dictionary for JSON serialization"""
        return {
            "success": self.success,
            "response": self.response,
            "mode_used": self.mode_used.value if hasattr(self.mode_used, 'value') else str(self.mode_used),
            "processing_time": self.processing_time,
            "resources_used": self.resources_used,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "verification_status": self.verification_status,
            "execution_plan": self.execution_plan,
            "session_id": self.session_id
        }"""
                )
                content = fixed_content
            
            # Fix 2: Ensure BrainResponse objects are properly serialized when sent
            if "str(brain_response)" in content:
                fixed_content = content.replace(
                    "str(brain_response)",
                    "brain_response.to_dict() if hasattr(brain_response, 'to_dict') else str(brain_response)"
                )
                content = fixed_content
            
            # Fix 3: Add a utility function to serialize BrainResponse objects
            if "def serialize_brain_response" not in content:
                import_index = content.find("import")
                if import_index >= 0:
                    # Find a good spot after imports to add our serialization function
                    lines = content.split('\n')
                    import_section_end = 0
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            import_section_end = i
                    
                    # Add serialization function after imports
                    serializer_code = """
def serialize_brain_response(response):
    """Utility function to serialize BrainResponse objects to JSON"""
    if hasattr(response, 'to_dict'):
        return response.to_dict()
    elif isinstance(response, dict):
        return response
    else:
        # Try to extract meaningful information from string representation
        if isinstance(response, str) and 'BrainResponse(' in response:
            # Simplified extraction to avoid complex parsing
            try:
                # Extract key attributes with basic string manipulation
                success = 'success=True' in response
                
                # Extract response text
                response_start = response.find('response="') + 10
                response_end = response.find('"', response_start)
                response_text = response[response_start:response_end] if response_start > 10 else "Error extracting response"
                
                # Basic metadata
                return {
                    "success": success,
                    "response": response_text,
                    "mode_used": "unknown",
                    "processing_time": 0.0,
                    "resources_used": [],
                    "confidence": 0.0,
                    "metadata": {},
                    "verification_status": "unknown"
                }
            except Exception as e:
                logger.error(f"Error parsing BrainResponse string: {e}")
                return {"success": False, "response": str(response)}
        return {"success": True, "response": str(response)}
"""
                    lines.insert(import_section_end + 1, serializer_code)
                    content = '\n'.join(lines)
            
            # Fix 4: Replace websocket send code to use the serializer
            if "await websocket.send(json.dumps({'type': 'response', 'response': " in content:
                fixed_content = content.replace(
                    "await websocket.send(json.dumps({'type': 'response', 'response': ",
                    "await websocket.send(json.dumps({'type': 'response', 'data': serialize_brain_response("
                )
                content = fixed_content
            
            # Write the fixed content back
            with open(file_path, 'w') as f:
                f.write(content)
                
            logger.info(f"✅ Fixed {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error fixing {file_path}: {e}")

def fix_bridge_server():
    """Fix bridge server to properly handle BrainResponse objects"""
    
    bridge_path = "overlay/fixed_bridge_server.py"
    if not os.path.exists(bridge_path):
        logger.warning(f"Bridge server not found: {bridge_path}")
        return
    
    logger.info(f"Fixing bridge server: {bridge_path}...")
    
    try:
        with open(bridge_path, 'r') as f:
            content = f.read()
        
        # Add BrainResponse handling to bridge server
        if "def handle_brain_response" not in content:
            # Find a good spot to add our function
            handler_index = content.find("async def handler")
            if handler_index >= 0:
                # Add the handler function before the main handler
                handler_code = """
def handle_brain_response(data):
    """Handle BrainResponse objects and convert to proper format"""
    if isinstance(data, dict) and 'response' in data and isinstance(data['response'], str) and 'BrainResponse(' in data['response']:
        # Try to extract the actual response content
        try:
            response_start = data['response'].find('response="') + 10
            response_end = data['response'].find('"', response_start)
            
            if response_start > 10 and response_end > response_start:
                # Extract the actual response text
                response_text = data['response'][response_start:response_end]
                
                # Replace with extracted text
                data['response'] = response_text
                
                # Also extract mode if available
                mode_start = data['response'].find('mode_used=') + 10
                if mode_start > 10:
                    mode_end = data['response'].find(',', mode_start)
                    if mode_end > mode_start:
                        mode_text = data['response'][mode_start:mode_end].strip()
                        if mode_text:
                            data['mode'] = mode_text
        except Exception as e:
            logger.error(f"Error extracting from BrainResponse: {e}")
    
    return data
"""
                content = content[:handler_index] + handler_code + content[handler_index:]
        
        # Modify the websocket message handling to use our function
        if "data = json.loads(event.data)" in content and "handle_brain_response(data)" not in content:
            fixed_content = content.replace(
                "data = json.loads(event.data)",
                "data = json.loads(event.data)\n                          data = handle_brain_response(data)"
            )
            content = fixed_content
        
        # Write the fixed content back
        with open(bridge_path, 'w') as f:
            f.write(content)
            
        logger.info(f"✅ Fixed bridge server: {bridge_path}")
        
    except Exception as e:
        logger.error(f"❌ Error fixing bridge server: {e}")

def main():
    """Main function to fix BrainResponse serialization issues"""
    logger.info("🔧 Starting BrainResponse serialization fix...")
    
    # Fix backend files
    fix_backend_files()
    
    # Fix bridge server
    fix_bridge_server()
    
    logger.info("✅ Fix completed! Please restart your backend and bridge servers.")
    logger.info("Restart commands:")
    logger.info("1. Stop current servers: ./STOP_FIXED_SYSTEM.sh")
    logger.info("2. Start servers again: ./START_FIXED_SYSTEM.sh")

if __name__ == "__main__":
    main()