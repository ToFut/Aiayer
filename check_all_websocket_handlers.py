#!/usr/bin/env python3
"""
Script to check and fix all WebSocket handlers in the project
"""
import os
import re
import sys
import shutil

def find_handler_files():
    """Find files that likely contain WebSocket handlers"""
    handler_files = []
    
    # Define directories to search
    search_dirs = ['.', 'agent', 'utils', 'bridge']
    
    for dir_path in search_dirs:
        if not os.path.exists(dir_path):
            continue
            
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Check if file contains WebSocket server code
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    if ('import websockets' in content or 'from websockets' in content) and 'websockets.serve' in content:
                        handler_files.append(file_path)
    
    return handler_files

def check_and_fix_file(file_path):
    """Check and fix handler signatures in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = file_path + ".ws_fix_bak"
    shutil.copy2(file_path, backup_path)
    
    # Look for handler function definitions
    # Various patterns for handler functions
    patterns = [
        # Class methods with only websocket parameter
        r'(async\s+def\s+[\w_]+\s*\(\s*self\s*,\s*websocket\s*\)\s*:)',
        # Class methods with other single parameters (like 'connection')
        r'(async\s+def\s+[\w_]+\s*\(\s*self\s*,\s*connection\s*\)\s*:)',
        # Regular functions with only websocket parameter
        r'(async\s+def\s+[\w_]+\s*\(\s*websocket\s*\)\s*:)',
        # Regular functions with other single parameters
        r'(async\s+def\s+[\w_]+\s*\(\s*connection\s*\)\s*:)'
    ]
    
    # Check for potential issue with serve(handler, ...) calls
    serve_calls = re.findall(r'(websockets\.serve\s*\(\s*\w+[\w\.]*\s*,)', content)
    
    # Check for lines around handlers that have websockets.serve to identify potential handler functions
    serve_lines = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'websockets.serve' in line:
            # Extract the handler name - try to identify which function is being passed
            handler_match = re.search(r'websockets\.serve\s*\(\s*(\w+[\w\.]*)\s*,', line)
            if handler_match:
                handler_name = handler_match.group(1)
                serve_lines.append((i, line, handler_name))
    
    # Print findings
    changes_needed = False
    
    # Check handler function definitions
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            print(f"Potential issue found in {file_path}:")
            print(f"  {match}")
            changes_needed = True
            
            # Fix: Add path parameter
            new_def = match.rstrip(':')
            if new_def.endswith(')'):
                new_def = new_def[:-1] + ', path)'
            new_def += ':'
            
            content = content.replace(match, new_def)
    
    # Check serve calls
    if serve_calls:
        print(f"Found {len(serve_calls)} websockets.serve calls in {file_path}:")
        for call in serve_calls:
            print(f"  {call}...")
    
    if serve_lines:
        print(f"Handler functions used in websockets.serve in {file_path}:")
        for line_num, line, handler_name in serve_lines:
            print(f"  Line {line_num+1}: {handler_name} in {line.strip()}")
    
    # Write changes if needed
    if changes_needed:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"✓ No issues found in {file_path}")
        # Remove backup if no changes needed
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return False

def main():
    """Main function"""
    print("Checking for WebSocket handler issues...")
    
    handler_files = find_handler_files()
    print(f"Found {len(handler_files)} files with potential WebSocket handlers")
    
    fixed_count = 0
    for file_path in handler_files:
        if check_and_fix_file(file_path):
            fixed_count += 1
    
    if fixed_count > 0:
        print(f"\n✅ Fixed {fixed_count} files with potential WebSocket handler issues")
        print("Please restart your application to apply the fixes")
    else:
        print("\n✓ No WebSocket handler issues found or fixed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())