#!/usr/bin/env python3
"""
Debug script to identify and fix screen sharing issues.
"""

import asyncio
import json
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_screen_sharing_backend():
    """Check if backend components are properly configured for screen sharing."""
    
    logger.info("🔍 Checking Backend Screen Sharing Configuration...")
    
    # Check if enhanced backend has screen sharing handlers
    backend_files = [
        "/Users/segevbin/Desktop/SensAI/Aiayer/enhanced_enterprise_backend_with_context.py",
        "/Users/segevbin/Desktop/SensAI/Aiayer/enterprise_backend_8767.py",
        "/Users/segevbin/Desktop/SensAI/Aiayer/realtime_screen_tcp_server.py"
    ]
    
    for backend_file in backend_files:
        if Path(backend_file).exists():
            logger.info(f"✅ Found backend file: {Path(backend_file).name}")
            
            with open(backend_file, 'r') as f:
                content = f.read()
                
                # Check for screen sharing handlers
                if 'start_screen_sharing' in content:
                    logger.info(f"   ✅ Has start_screen_sharing handler")
                else:
                    logger.warning(f"   ⚠️  Missing start_screen_sharing handler")
                
                if 'screen_frame' in content:
                    logger.info(f"   ✅ Has screen_frame handling")
                else:
                    logger.warning(f"   ⚠️  Missing screen_frame handling")
        else:
            logger.warning(f"❌ Backend file not found: {Path(backend_file).name}")
    
    return True

def check_frontend_integration():
    """Check if frontend properly integrates screen sharing."""
    
    logger.info("🎨 Checking Frontend Screen Sharing Integration...")
    
    # Check ScreenViewer component
    screen_viewer_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/ScreenViewer.svelte")
    if screen_viewer_path.exists():
        with open(screen_viewer_path, 'r') as f:
            content = f.read()
            
            if 'on:close' in content:
                logger.info("✅ ScreenViewer has close handler")
            else:
                logger.warning("⚠️  ScreenViewer missing close handler")
                
            if 'bridge' in content:
                logger.info("✅ ScreenViewer accepts bridge prop")
            else:
                logger.warning("⚠️  ScreenViewer missing bridge prop")
    else:
        logger.error("❌ ScreenViewer component not found")
        return False
    
    # Check NextGenAppleChatWidget integration
    chat_widget_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte")
    if chat_widget_path.exists():
        with open(chat_widget_path, 'r') as f:
            content = f.read()
            
            checks = [
                ('ScreenViewer import', 'import ScreenViewer'),
                ('showScreenViewer state', 'showScreenViewer'),
                ('toggleScreenViewer function', 'toggleScreenViewer'),
                ('screen-share-btn', 'screen-share-btn'),
                ('screen-viewer-modal', 'screen-viewer-modal'),
                ('bridgeWrapper', 'bridgeWrapper')
            ]
            
            for check_name, search_term in checks:
                if search_term in content:
                    logger.info(f"✅ {check_name} found")
                else:
                    logger.error(f"❌ {check_name} MISSING")
                    return False
    else:
        logger.error("❌ NextGenAppleChatWidget not found")
        return False
    
    logger.info("✅ Frontend integration looks good")
    return True

def create_debug_websocket_handler():
    """Create a debug WebSocket message handler for the backend."""
    
    logger.info("🔧 Creating Debug WebSocket Handler...")
    
    debug_handler = '''
# Add this to your backend WebSocket message handler

async def handle_screen_sharing_request(websocket, data):
    """Handle screen sharing requests with debug logging."""
    print(f"🖥️  Screen sharing request received: {data}")
    
    try:
        # Import screen capture functionality
        from realtime_screen_tcp_server import RealtimeScreenTCPServer
        
        # Create or get screen server instance
        if not hasattr(websocket, 'screen_server'):
            websocket.screen_server = RealtimeScreenTCPServer()
            await websocket.screen_server.start()
        
        # Get compressed frame data
        frame_data = websocket.screen_server.get_compressed_frame_data()
        
        if frame_data:
            # Send frame to client
            await websocket.send(json.dumps(frame_data))
            print(f"✅ Screen frame sent: {frame_data['width']}x{frame_data['height']}")
        else:
            print("⚠️  No screen frame data available")
            await websocket.send(json.dumps({
                "type": "screen_sharing_error",
                "message": "No screen data available"
            }))
            
    except Exception as e:
        print(f"❌ Screen sharing error: {e}")
        await websocket.send(json.dumps({
            "type": "screen_sharing_error", 
            "message": str(e)
        }))

# Add to your WebSocket message router:
if message_type == "start_screen_sharing":
    await handle_screen_sharing_request(websocket, data)
'''
    
    debug_file = Path("/Users/segevbin/Desktop/SensAI/Aiayer/debug_websocket_screen_sharing.py")
    with open(debug_file, 'w') as f:
        f.write(debug_handler)
    
    logger.info(f"✅ Debug handler created: {debug_file}")
    return debug_file

def create_simple_test_page():
    """Create a simple test page to debug screen sharing."""
    
    logger.info("🧪 Creating Simple Test Page...")
    
    test_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screen Sharing Debug Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .button { padding: 10px 20px; margin: 10px; background: #007AFF; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .button:hover { background: #0056CC; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        #log { height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🖥️ Screen Sharing Debug Test</h1>
    
    <div id="status" class="status info">Not connected</div>
    
    <button class="button" onclick="connect()">Connect to Backend</button>
    <button class="button" onclick="requestScreenSharing()">Request Screen Sharing</button>
    <button class="button" onclick="clearLog()">Clear Log</button>
    
    <div id="log"></div>
    
    <script>
        let ws = null;
        
        function log(message, type = 'info') {
            const logDiv = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            logDiv.innerHTML += `<div style="color: ${type === 'error' ? 'red' : type === 'success' ? 'green' : 'black'}">[${timestamp}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function updateStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
        }
        
        function connect() {
            log('Attempting to connect to WebSocket...');
            
            try {
                ws = new WebSocket('ws://localhost:8765');
                
                ws.onopen = () => {
                    log('✅ Connected to WebSocket!', 'success');
                    updateStatus('Connected', 'success');
                };
                
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        log(`📨 Received: ${JSON.stringify(data)}`, 'success');
                        
                        if (data.type === 'screen_frame') {
                            log(`🖥️ Screen frame received: ${data.width}x${data.height} @ ${data.fps}fps`, 'success');
                        } else if (data.type === 'screen_sharing_error') {
                            log(`❌ Screen sharing error: ${data.message}`, 'error');
                        }
                    } catch (e) {
                        log(`❌ Error parsing message: ${e}`, 'error');
                    }
                };
                
                ws.onerror = (error) => {
                    log(`❌ WebSocket error: ${error}`, 'error');
                    updateStatus('Connection Error', 'error');
                };
                
                ws.onclose = () => {
                    log('🔌 WebSocket connection closed');
                    updateStatus('Disconnected', 'info');
                };
                
            } catch (error) {
                log(`❌ Connection failed: ${error}`, 'error');
                updateStatus('Connection Failed', 'error');
            }
        }
        
        function requestScreenSharing() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('❌ Not connected to WebSocket', 'error');
                return;
            }
            
            log('📺 Requesting screen sharing...');
            
            const request = {
                type: 'start_screen_sharing',
                timestamp: Date.now()
            };
            
            ws.send(JSON.stringify(request));
            log(`📤 Sent request: ${JSON.stringify(request)}`);
        }
        
        function clearLog() {
            document.getElementById('log').innerHTML = '';
        }
        
        // Auto-connect on page load
        window.onload = () => {
            log('🚀 Screen Sharing Debug Test started');
        };
    </script>
</body>
</html>'''
    
    test_file = Path("/Users/segevbin/Desktop/SensAI/Aiayer/test_screen_sharing.html")
    with open(test_file, 'w') as f:
        f.write(test_html)
    
    logger.info(f"✅ Test page created: {test_file}")
    logger.info("📝 Open this file in your browser to test WebSocket screen sharing")
    return test_file

def main():
    """Main debug function."""
    
    logger.info("🔍 Starting Screen Sharing Debug Session...")
    
    # Run checks
    check_screen_sharing_backend()
    frontend_ok = check_frontend_integration()
    
    if frontend_ok:
        logger.info("✅ Frontend integration appears correct")
    else:
        logger.error("❌ Frontend integration has issues")
    
    # Create debug tools
    debug_handler_file = create_debug_websocket_handler()
    test_page_file = create_simple_test_page()
    
    logger.info("\n" + "="*60)
    logger.info("🎯 DEBUG RECOMMENDATIONS:")
    logger.info("="*60)
    
    logger.info("1. Check if backend is running:")
    logger.info("   ps aux | grep python | grep backend")
    
    logger.info("\n2. Test WebSocket connection:")
    logger.info(f"   open {test_page_file}")
    
    logger.info("\n3. Check browser console:")
    logger.info("   - Open DevTools (F12)")
    logger.info("   - Look for JavaScript errors")
    logger.info("   - Check Network tab for WebSocket connection")
    
    logger.info("\n4. Add debug handler to backend:")
    logger.info(f"   - Copy code from: {debug_handler_file}")
    logger.info("   - Add to your WebSocket message handler")
    
    logger.info("\n5. Check backend logs:")
    logger.info("   - Look for 'start_screen_sharing' messages")
    logger.info("   - Check for screen capture errors")
    
    logger.info("\n6. Test screen capture directly:")
    logger.info("   python -c \"from realtime_screen_tcp_server import RealtimeScreenTCPServer; server = RealtimeScreenTCPServer(); print(server.get_compressed_frame_data())\"")
    
    logger.info("\n" + "="*60)
    logger.info("🚀 Start debugging with the test page!")
    logger.info("="*60)

if __name__ == "__main__":
    main()