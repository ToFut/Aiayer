#!/usr/bin/env python3
"""
Minimal WebSocket server with proper handler signature.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minimal_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_ws')

# Connected clients
connected_clients = set()

# Handler supports both legacy and modern websockets versions
async def handler(websocket, path=None):
    """WebSocket handler supporting both websockets versions
    - For legacy websockets: handler(websocket, path)
    - For modern websockets: handler(websocket) where path is available as websocket.path
    """
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    
    # Handle both old and new websockets versions
    if path is None and hasattr(websocket, 'path'):
        path = websocket.path
    elif path is None:
        path = "/"
        
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to minimal WebSocket server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Start data sending task
        data_task = asyncio.create_task(send_periodic_data(websocket))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Handle specific message types
                message_type = data.get('type', 'unknown')
                
                if message_type == 'agent_confirmation':
                    # Handle agent confirmation message (DO button)
                    logger.info(f"⚡ Agent confirmation received: {data}")
                    
                    # Extract session_id and action
                    session_id = data.get('session_id', '')
                    action = data.get('action', '').upper()
                    
                    # Send immediate progress update
                    await websocket.send(json.dumps({
                        "type": "agent_progress",
                        "session_id": session_id,
                        "step": 1,
                        "progress": 20,
                        "message": "🚀 Execution started: Analyzing screen..."
                    }))
                    
                    # Wait a short time to simulate processing
                    await asyncio.sleep(1)
                    
                    # Send another progress update
                    await websocket.send(json.dumps({
                        "type": "agent_progress",
                        "session_id": session_id,
                        "step": 2,
                        "progress": 60,
                        "message": "⚡ Executing automation steps..."
                    }))
                    
                    # Wait a short time to simulate execution
                    await asyncio.sleep(1.5)
                    
                    # Send completion message
                    await websocket.send(json.dumps({
                        "type": "agent_execution_success",
                        "session_id": session_id,
                        "result": {
                            "success": True,
                            "steps_executed": 3,
                            "execution_time": 2.5
                        },
                        "summary": "Execution completed successfully. All steps were performed as planned.",
                        "execution_completed": True
                    }))
                
                elif message_type == 'do_button':
                    # Handle DO button display request
                    logger.info(f"📢 DO button display request received: {data}")
                    
                    # Extract content
                    content = data.get('content', {})
                    title = content.get('title', 'Suggestion')
                    message = content.get('message', 'Would you like help with this?')
                    buttons = content.get('buttons', [])
                    
                    # Log the DO button info
                    logger.info(f"DO Button: {title} - {message}")
                    
                    # Echo back acknowledgement that we received the request
                    await websocket.send(json.dumps({
                        "type": "suggestion_displayed",
                        "title": title,
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                        "display_id": f"suggestion_{int(time.time())}"
                    }))
                    
                    # Create direct chat message in the EXACT format expected by EnterpriseChatWidget
                    # This is the key change - using the format that the widget actually expects
                    direct_message = {
                        "success": True,
                        "response": f"💡 {title}: {message}",
                        "mode": "SUGGEST",
                        "processing_time": 0.5,
                        "enterprise_validated": True,
                        "buttons": [
                            {
                                "id": "do_it",
                                "text": "Yes, help me",
                                "action": "accept",
                                "style": "success"
                            },
                            {
                                "id": "dismiss",
                                "text": "No thanks",
                                "action": "dismiss",
                                "style": "danger"
                            }
                        ],
                        "interactive": True
                    }
                    
                    # Send the properly formatted message to the overlay
                    await websocket.send(json.dumps(direct_message))
                    logger.info(f"✅ Sent properly formatted suggestion to overlay UI")
                    
                    logger.info(f"✅ Sent suggestion to overlay UI")
                    
                else:
                    # Default response for other message types
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "message": f"Received your {message_type} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed with {client_id}")
    except Exception as e:
        logger.error(f"Error with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        data_task.cancel()
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket):
    """Send periodic data to client"""
    try:
        import random
        counter = 0
        
        while True:
            # Create simulated data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 234.5},
                {"name": "VS Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 412.8},
                {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 78.3}
            ]
            
            # Rotate active app
            apps = ["Chrome", "VS Code", "Terminal", "Finder"]
            active_app = apps[counter % len(apps)]
            
            screen_data = {
                "active_app": active_app,
                "window_title": f"{active_app} - Working on project",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send sensor data
            sensor_data = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(sensor_data))
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug("Data sending task canceled")
    except Exception as e:
        logger.error(f"Error sending data: {e}")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Create a server that works with both websockets versions
    try:
        # Try the legacy style
        server = await websockets.serve(handler, host, port)
        logger.info(f"WebSocket server created with legacy websockets style")
    except Exception as e:
        logger.warning(f"Could not create server with legacy style: {e}")
        # Try the modern style
        try:
            from websockets.server import serve
            server = await serve(handler, host, port)
            logger.info(f"WebSocket server created with modern websockets style")
        except Exception as e2:
            logger.error(f"Could not create server with either style: {e2}")
            raise
    
    with open('pids/ws_server.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"Server started on ws://{host}:{port}")
    
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
