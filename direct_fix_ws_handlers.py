#!/usr/bin/env python3
"""
Direct fix for WebSocket handlers in multiple files
"""
import os
import re
import sys
import shutil

# Files to check - these are the most likely candidates based on the error
files_to_check = [
    "agent/overlay_bridge.py",
    "utils/enhanced_server.py",
    "utils/simple_server.py",
    "bridge/server.py",
    "simplified_overlay.py"
]

def fix_handler_in_file(file_path):
    """Fix handler signatures in a file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = file_path + ".path_fix_bak"
    print(f"Creating backup at {backup_path}")
    shutil.copy2(file_path, backup_path)
    
    # Look for missing path parameters in handler functions
    orig_content = content
    
    # Pattern for class method handlers with missing path parameter
    content = re.sub(
        r'async\s+def\s+([\w_]+)\s*\(\s*self\s*,\s*websocket\s*\)\s*:',
        r'async def \1(self, websocket, path):',
        content
    )
    
    # Pattern for regular function handlers with missing path parameter
    content = re.sub(
        r'async\s+def\s+([\w_]+)\s*\(\s*websocket\s*\)\s*:',
        r'async def \1(websocket, path):',
        content
    )
    
    # Check for connection parameter too (some code might use different names)
    content = re.sub(
        r'async\s+def\s+([\w_]+)\s*\(\s*self\s*,\s*connection\s*\)\s*:',
        r'async def \1(self, connection, path):',
        content
    )
    
    # Regular functions with connection parameter
    content = re.sub(
        r'async\s+def\s+([\w_]+)\s*\(\s*connection\s*\)\s*:',
        r'async def \1(connection, path):',
        content
    )
    
    if content != orig_content:
        print(f"✅ Fixed handlers in {file_path}")
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

def main():
    """Main function"""
    print("Directly fixing WebSocket handlers in specific files...")
    
    fixed_count = 0
    for file_path in files_to_check:
        if fix_handler_in_file(file_path):
            fixed_count += 1
    
    if fixed_count > 0:
        print(f"\n✅ Fixed {fixed_count} files with WebSocket handler issues")
        print("Please restart your application to apply the fixes")
    else:
        print("\n✓ No WebSocket handler issues found or fixed in the target files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())