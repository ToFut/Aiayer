#!/usr/bin/env python3
"""
Script to fix the overlay_bridge.py file by ensuring the handler method has the path parameter
"""
import os
import shutil
import re
import sys

def fix_overlay_bridge():
    # Path to the overlay_bridge.py file
    overlay_bridge_path = os.path.join("agent", "overlay_bridge.py")
    
    # Check if the file exists
    if not os.path.exists(overlay_bridge_path):
        print(f"Error: {overlay_bridge_path} not found!")
        return False
    
    # Create a backup
    backup_path = overlay_bridge_path + ".bak"
    print(f"Creating backup at {backup_path}")
    shutil.copy2(overlay_bridge_path, backup_path)
    
    # Read the file
    with open(overlay_bridge_path, 'r') as f:
        content = f.read()
    
    # Check if the handler method already has the path parameter
    handler_method_pattern = r"async\s+def\s+_handler\s*\(\s*self\s*,\s*websocket\s*\)\s*:"
    if not re.search(handler_method_pattern, content):
        print("Could not find the handler method with the expected signature.")
        print("The method might already have the path parameter or it has a different name.")
        return False
    
    # Replace the handler method signature
    fixed_content = re.sub(
        handler_method_pattern,
        "async def _handler(self, websocket, path):",
        content
    )
    
    # Check if any replacement was made
    if fixed_content == content:
        print("No changes were made. The pattern might not match.")
        return False
    
    # Write the fixed content back to the file
    with open(overlay_bridge_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Successfully fixed {overlay_bridge_path}")
    print("The handler method now includes the required 'path' parameter.")
    return True

if __name__ == "__main__":
    if fix_overlay_bridge():
        print("Fix applied successfully. Try running your system again.")
        sys.exit(0)
    else:
        print("Fix could not be applied automatically.")
        sys.exit(1)