#!/usr/bin/env python3
"""
Enterprise Overlay Launcher
Launches the enterprise chat overlay that connects to the backend on port 8767
"""

import asyncio
import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def check_backend_running():
    """Check if the enterprise backend is running on port 8767"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8767))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_backend():
    """Start the enterprise backend server"""
    print("🚀 Starting Enterprise Backend Server...")
    
    backend_script = Path(__file__).parent / "enterprise_backend_server.py"
    
    # Start backend in background
    process = subprocess.Popen([
        sys.executable, str(backend_script)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    return process

def launch_overlay():
    """Launch the enterprise chat overlay"""
    overlay_file = Path(__file__).parent / "enterprise_overlay_chat.html"
    
    if not overlay_file.exists():
        print("❌ Overlay file not found!")
        return False
    
    # Open the HTML file in the default browser
    print("🎯 Launching Enterprise Chat Overlay...")
    webbrowser.open(f"file://{overlay_file.absolute()}")
    
    return True

def main():
    """Main launcher function"""
    print("🏢 Enterprise SensAI Overlay Launcher")
    print("=" * 50)
    
    # Check if backend is already running
    if check_backend_running():
        print("✅ Backend server is already running on port 8767")
    else:
        print("⚠️  Backend server not detected, starting it...")
        backend_process = start_backend()
        
        # Wait and verify backend started
        for i in range(10):  # Wait up to 10 seconds
            if check_backend_running():
                print("✅ Backend server started successfully!")
                break
            time.sleep(1)
            print(f"   Waiting for backend... ({i+1}/10)")
        else:
            print("❌ Failed to start backend server")
            return False
    
    # Launch the overlay
    if launch_overlay():
        print("🎉 Enterprise Chat Overlay launched!")
        print("\n📋 Instructions:")
        print("1. The overlay should open in your browser")
        print("2. Choose a mode: Ask, Agent, Suggest, or General")
        print("3. Type your message and press Enter")
        print("4. The overlay connects to ws://127.0.0.1:8767")
        print("\n🎯 Available Modes:")
        print("   🤔 ASK MODE - Questions with memory context")
        print("   🤖 AGENT MODE - Task planning and execution")  
        print("   💡 SUGGEST MODE - Proactive recommendations")
        print("   💬 GENERAL MODE - Casual conversation")
        print("\n🔧 Troubleshooting:")
        print("   - If overlay doesn't connect, check backend logs")
        print("   - Server logs: tail -f enterprise_server.log")
        print("   - Test backend: python focused_quality_test.py")
        return True
    else:
        print("❌ Failed to launch overlay")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✨ Enterprise SensAI is ready!")
            print("Press Ctrl+C to stop the backend server")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                
                # Try to kill backend process
                try:
                    subprocess.run(["pkill", "-f", "enterprise_backend_server.py"], 
                                 capture_output=True)
                    print("✅ Backend server stopped")
                except:
                    print("⚠️  Please manually stop the backend if still running")
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)