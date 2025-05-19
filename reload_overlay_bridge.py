#!/usr/bin/env python3
"""
Script to reload the overlay_bridge module with fixed handler signature
"""
import os
import sys
import importlib
import shutil

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Make a backup of the original file
    overlay_bridge_path = os.path.join("agent", "overlay_bridge.py")
    backup_path = overlay_bridge_path + ".bak" + str(os.getpid())
    
    if os.path.exists(overlay_bridge_path):
        print(f"Creating backup at {backup_path}")
        shutil.copy2(overlay_bridge_path, backup_path)
    
    # Check if the module exists and is imported
    if "agent.overlay_bridge" in sys.modules:
        print("Module agent.overlay_bridge is already imported, reloading...")
        # Force reload of the module
        importlib.reload(sys.modules["agent.overlay_bridge"])
    
    print("Verifying module...")
    from agent.overlay_bridge import OverlayBridge
    
    # Create a test instance to verify
    bridge = OverlayBridge()
    
    # Check if the _handler method has the correct signature
    import inspect
    handler_signature = inspect.signature(bridge._handler)
    parameters = list(handler_signature.parameters.keys())
    
    print(f"Handler parameters: {parameters}")
    
    if 'path' not in parameters:
        print("ERROR: The path parameter is missing from the handler method!")
        print("Manual fix needed - ensure _handler method in overlay_bridge.py has the path parameter:")
        print("async def _handler(self, websocket, path):")
        sys.exit(1)
    
    print("✅ The overlay_bridge module is properly configured with path parameter.")
    
    # Double check and fix if needed
    with open(overlay_bridge_path, 'r') as f:
        content = f.read()
    
    # Update any outdated uses if necessary (check async with websockets.serve call)
    if "async with websockets.serve(self._handler," in content:
        print("Handler is used correctly in websockets.serve.")
    
    print("Module verification complete!")
    print("You can now try running your system again.")
    
except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)