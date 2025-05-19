#!/usr/bin/env python3
"""
Update Bridge URL

This script updates the WebSocket URL in the overlay bridge.js file
to use the interceptor server on port 8766 for reliable responses.
"""
import os
import sys
import re
import shutil
import argparse
from datetime import datetime

def update_bridge_file(bridge_file, target_port):
    """Update the WebSocket URL in the bridge file."""
    # First, create a backup
    backup_file = f"{bridge_file}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(bridge_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    with open(bridge_file, 'r') as f:
        content = f.read()
    
    # Replace the WebSocket URL
    new_content = re.sub(
        r"this\.ws\s*=\s*new\s*WebSocket\('ws://localhost:\d+'\);",
        f"this.ws = new WebSocket('ws://localhost:{target_port}');",
        content
    )
    
    with open(bridge_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated WebSocket URL to port {target_port} in {bridge_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Update WebSocket port in overlay bridge.js")
    parser.add_argument('--port', type=int, default=8766, help="Target WebSocket port (default: 8766)")
    parser.add_argument('--reset', action='store_true', help="Reset to original port (8765)")
    args = parser.parse_args()
    
    # Define bridge file path
    bridge_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "overlay", "src", "services", "bridge.js"
    )
    
    if not os.path.exists(bridge_file):
        print(f"Error: Bridge file not found at {bridge_file}")
        sys.exit(1)
    
    port = 8765 if args.reset else args.port
    
    try:
        if update_bridge_file(bridge_file, port):
            print(f"Successfully {'reset' if args.reset else 'updated'} WebSocket URL to port {port}")
        else:
            print("No changes were made.")
    except Exception as e:
        print(f"Error updating bridge file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()