#!/bin/bash

# Create necessary directories
mkdir -p logs/llm pids cache/process_sensor cache/screen_sensor cache/file_sensor

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f 'fixed_bridge_server.py|ollama_service.py'
sleep 1

# Make sure the port is free
if lsof -i:8765 &>/dev/null; then
    echo "Port 8765 is in use. Killing process..."
    lsof -ti:8765 | xargs kill -9
    sleep 1
fi

# Create a fixed version of our bridge server to handle LLM requests properly
echo "Creating fixed bridge server..."

cat > fixed_bridge_server_new.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_bridge')

# Track connected clients
connected_clients = set()
llm_service = None
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

# IMPORTANT: The handler MUST accept both websocket AND path parameters
async def handler(websocket, path):
    """WebSocket connection handler with the correct signature including path parameter"""
    global llm_service
    client_id = f"client_{id(websocket)}"
    client_type = "unknown"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to Aiayer system. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send initial sensor data (if we have any)
        if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client', 'unknown')
                    logger.info(f"Client {client_id} identified as: {client_type}")
                    
                    # If this is the LLM service connecting, save the reference
                    if 'ollama_llm_service' in client_type:
                        llm_service = websocket
                        logger.info("LLM service connected and registered")
                    
                    # Send ready confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "server_time": datetime.now().isoformat(),
                            "capabilities": ["context_tracking", "suggestions", "memory", "llm"]
                        }
                    }))
                    
                elif msg_type == 'process_data':
                    # Store process data from sensor
                    sensor_data["processes"] = data.get('payload', [])
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'screen_data':
                    # Store screen data from sensor
                    sensor_data["screen"] = data.get('payload', {})
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'file_data':
                    # Store file data from sensor
                    sensor_data["files"] = data.get('payload', [])
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'llm_request':
                    # Forward to LLM system if we have one connected
                    logger.info(f"LLM request received: {data.get('payload', {}).get('query', 'empty')}")
                    
                    if llm_service and llm_service in connected_clients:
                        # Forward the request to the LLM service
                        logger.info(f"Forwarding request to LLM service")
                        await llm_service.send(json.dumps(data))
                    else:
                        # No LLM service connected, send simulated response
                        logger.warning("No LLM service connected, sending simulated response")
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "response": "This is a simulated LLM response. No LLM service is connected to the system.",
                                "model": "simulator",
                                "context_used": True,
                                "processing_time": 0.5
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif msg_type == 'llm_response':
                    # Forward LLM response to all clients except the LLM service
                    logger.info("Received LLM response, forwarding to clients")
                    
                    # Forward to all clients except the LLM service
                    for client in connected_clients:
                        if client != llm_service:
                            await client.send(json.dumps(data))
                
                else:
                    # Default echo response
                    response = {
                        "type": "echo",
                        "payload": {
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if websocket == llm_service:
            llm_service = None
            logger.info("LLM service disconnected")
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients),
                    "llm_service_connected": llm_service is not None and llm_service in connected_clients
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    # Bind to localhost on port 8765 (for overlay connections)
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    
    # VERY IMPORTANT: The handler must have 2 parameters (websocket, path)
    # Make sure the handler is properly wrapped to include path parameter
    async def handler_wrapper(websocket, path):
        await handler(websocket, path)
    
    # Use serve with the wrapped handler to ensure correct signature
    server = await websockets.serve(handler_wrapper, host, port)
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
    logger.info(f"Heartbeat system active")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
EOF

chmod +x fixed_bridge_server_new.py

# Create a fixed version of ollama service
echo "Creating fixed ollama service..."

cat > ollama_service_fixed.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
import aiohttp
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/ollama_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ollama_service')

class OllamaLLM:
    def __init__(self, server_uri="ws://localhost:8765", ollama_url="http://localhost:11434"):
        self.server_uri = server_uri
        self.ollama_url = ollama_url
        self.model_name = "ollama:latest"  # Use the available model
        self.running = True
        self.context_data = {}
        
    async def generate_response(self, query, context=None):
        """Generate a response using Ollama API"""
        try:
            # Build context string from available data
            context_str = ""
            if context:
                if "screen" in context:
                    context_str += f"Active application: {context.get('screen', {}).get('active_app', 'unknown')}\n"
                
                if "processes" in context and context["processes"]:
                    context_str += "Running processes: "
                    proc_names = [p.get("name", "unknown") for p in context["processes"][:5]]
                    context_str += ", ".join(proc_names) + "\n"
            
            # Prepare prompt with context
            if context_str:
                prompt = f"Context information:\n{context_str}\n\nUser query: {query}"
            else:
                prompt = query
            
            logger.info(f"Sending request to Ollama API with model: {self.model_name}")
            logger.info(f"Prompt: {prompt[:100]}...")
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                start_time = datetime.now()
                logger.info(f"Calling Ollama API at {self.ollama_url}/api/generate")
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    logger.info(f"Ollama API response status: {resp.status}")
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return {
                            "response": f"Error generating response: {resp.status} - {error_text}",
                            "model": self.model_name,
                            "context_used": bool(context),
                            "processing_time": 0,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    result = await resp.json()
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Generated response in {processing_time:.2f}s")
                    logger.info(f"Response: {result.get('response', 'No response')[:100]}...")
                    
                    return {
                        "response": result.get("response", "No response generated"),
                        "model": self.model_name,
                        "context_used": bool(context),
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(traceback.format_exc())
            return {
                "response": f"Sorry, I encountered an error while generating a response: {str(e)}",
                "model": self.model_name,
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def connect_to_server(self):
        """Connect to the bridge server"""
        while self.running:
            try:
                logger.info(f"Connecting to bridge server at {self.server_uri}")
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "ollama_llm_service",
                            "version": "1.0.0",
                            "model": self.model_name,
                            "capabilities": ["text_generation", "context_aware"]
                        }
                    }))
                    
                    # Main message handling loop
                    while self.running:
                        try:
                            # Receive messages from server
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Process different message types
                            msg_type = data.get('type')
                            
                            if msg_type == 'sensor_data':
                                # Update context data from sensors
                                self.context_data = data.get('payload', {})
                                logger.debug("Context data updated")
                                
                            elif msg_type == 'llm_request':
                                # Process LLM request
                                payload = data.get('payload', {})
                                query = payload.get('query', '')
                                
                                logger.info(f"Processing LLM request: {query[:50]}...")
                                
                                # Generate response
                                llm_response = await self.generate_response(query, self.context_data)
                                
                                # Send response back
                                await websocket.send(json.dumps({
                                    "type": "llm_response",
                                    "payload": llm_response,
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                                logger.info(f"LLM response sent: {llm_response['response'][:50]}...")
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            logger.error(traceback.format_exc())
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def run(self):
        """Main method to run the LLM service"""
        logger.info(f"Starting Ollama LLM service with model {self.model_name}")
        
        # List available models
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        models = await resp.json()
                        logger.info(f"Available Ollama models: {models}")
                        
                        # Find a model to use
                        if models and "models" in models and models["models"]:
                            # Try to find latest model or default to first available
                            for model in models["models"]:
                                if "3.2" in model["name"]:
                                    self.model_name = model["name"]
                                    logger.info(f"Using model: {self.model_name}")
                                    break
                            else:
                                self.model_name = models["models"][0]["name"]
                                logger.info(f"Using model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/ollama_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to server
        await self.connect_to_server()

# Function to run the LLM service
async def run_ollama_service():
    llm = OllamaLLM()
    await llm.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_ollama_service())
    except KeyboardInterrupt:
        logger.info("Ollama service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Ollama service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
EOF

chmod +x ollama_service_fixed.py

# Start the bridge server
echo "Starting bridge server..."
python3 fixed_bridge_server_new.py > logs/bridge_server.log 2>&1 &
echo $! > pids/bridge_server.pid
sleep 2

# Check if bridge server started correctly
if [ -f pids/bridge_server.pid ] && ps -p $(cat pids/bridge_server.pid) > /dev/null; then
    echo "✅ Bridge server started successfully"
else
    echo "❌ Bridge server failed to start"
    exit 1
fi

# Start the Ollama service
echo "Starting Ollama LLM service..."
python3 ollama_service_fixed.py > logs/llm_service.log 2>&1 &
echo $! > pids/ollama_service.pid
sleep 2

# Check if Ollama service started correctly
if [ -f pids/ollama_service.pid ] && ps -p $(cat pids/ollama_service.pid) > /dev/null; then
    echo "✅ Ollama service started successfully"
else
    echo "❌ Ollama service failed to start"
    exit 1
fi

echo "System started successfully!"
echo "Run the following command to test:"
echo "python3 test_bridge_connection.py"