#!/usr/bin/env python3
"""
Memory Dashboard Server
Provides a web interface for viewing and managing the memory system.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/dashboard_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('dashboard_server')

# Create FastAPI app
app = FastAPI(title="Memory Dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web/dashboard/static"), name="static")

# Global variables
memory_system_ws = None
connected_clients = set()

@app.get("/")
async def get_dashboard():
    """Serve the dashboard HTML page."""
    return FileResponse("web/dashboard/test_dashboard.html")

@app.get("/api/memory/metrics")
async def get_memory_metrics():
    """Get current memory metrics."""
    if not memory_system_ws:
        return {"error": "Not connected to memory system"}
    
    try:
        # Request metrics from memory system
        await memory_system_ws.send(json.dumps({"type": "get_metrics"}))
        response = await memory_system_ws.recv()
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error getting memory metrics: {e}")
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections."""
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Forward message to memory system
            if memory_system_ws:
                await memory_system_ws.send(data)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)

async def connect_to_memory_system():
    """Connect to the memory system WebSocket server."""
    global memory_system_ws
    while True:
        try:
            async with websockets.connect("ws://localhost:8765") as websocket:
                memory_system_ws = websocket
                logger.info("Connected to memory system")
                
                while True:
                    try:
                        # Receive memory state updates
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Broadcast to all connected clients
                        for client in connected_clients:
                            try:
                                await client.send_text(message)
                            except Exception as e:
                                logger.error(f"Error broadcasting to client: {e}")
                                connected_clients.remove(client)
                        
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Connection to memory system closed")
                        break
                    except Exception as e:
                        logger.error(f"Error in memory system communication: {e}")
                        break
            
        except Exception as e:
            logger.error(f"Error connecting to memory system: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup."""
    asyncio.create_task(connect_to_memory_system())

def main():
    """Run the dashboard server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()