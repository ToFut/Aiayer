#!/usr/bin/env python3
"""
Check Overlay Connections - Verify which WebSocket servers the overlay is connecting to
"""
import asyncio
import websockets
import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket ports to check
WS_PORTS = [8765, 8766, 8767, 8768, 8769]

# Connected clients per port
connected_clients = {port: set() for port in WS_PORTS}

# Stats
connection_stats = {port: 0 for port in WS_PORTS}

async def run_test_server(port):
    """Run a test WebSocket server on the given port"""
    
    async def handler(websocket, path):
        """Handle WebSocket connections"""
        client_id = f"client_{id(websocket)}"
        connected_clients[port].add(client_id)
        connection_stats[port] += 1
        
        logger.info(f"Client {client_id} connected to port {port}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "server_name": f"Test Server on port {port}",
                "server_version": "1.0.0",
                "capabilities": ["testing"],
                "timestamp": datetime.now().isoformat()
            }))
            
            # Keep connection open
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    logger.info(f"Received message on port {port}: {message[:100]}...")
                    
                    # Send a response
                    await websocket.send(json.dumps({
                        "type": "test_response",
                        "message": f"Response from test server on port {port}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }))
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected from port {port}")
        
        finally:
            if client_id in connected_clients[port]:
                connected_clients[port].remove(client_id)
    
    # Start the server
    try:
        server = await websockets.serve(handler, "localhost", port)
        logger.info(f"Test server started on port {port}")
        return server
    except OSError as e:
        logger.error(f"Could not start server on port {port}: {e}")
        return None

async def main():
    """Main function"""
    logger.info("=== OVERLAY CONNECTION CHECKER ===")
    logger.info("Checking which WebSocket servers the overlay connects to")
    
    # Start test servers
    servers = []
    for port in WS_PORTS:
        server = await run_test_server(port)
        if server:
            servers.append((port, server))
    
    if not servers:
        logger.error("Could not start any test servers")
        return
    
    logger.info(f"Started {len(servers)} test servers")
    logger.info("Waiting for overlay connections...")
    logger.info("You may need to restart the overlay to trigger connections")
    
    # Wait for connections
    try:
        # Run for 30 seconds
        for i in range(30):
            await asyncio.sleep(1)
            
            # Print connection status
            if i % 5 == 0:
                logger.info("Connection status:")
                for port in WS_PORTS:
                    if connection_stats[port] > 0:
                        logger.info(f"  Port {port}: ✅ {connection_stats[port]} connections")
                    else:
                        logger.info(f"  Port {port}: ❌ No connections")
    
    finally:
        # Close servers
        for port, server in servers:
            server.close()
            await server.wait_closed()
        
        # Print final stats
        logger.info("=== FINAL CONNECTION STATISTICS ===")
        for port in WS_PORTS:
            if connection_stats[port] > 0:
                logger.info(f"Port {port}: ✅ {connection_stats[port]} connections")
            else:
                logger.info(f"Port {port}: ❌ No connections")
        
        # Print recommendations
        logger.info("\n=== RECOMMENDATIONS ===")
        if connection_stats[8766] > 0:
            logger.info("✅ Overlay is correctly connecting to the proxy bridge (port 8766)")
            logger.info("   Try sending a notification via the proxy bridge:")
            logger.info("   python3 /Users/segevbin/Desktop/SensAI/Aiayer/legacy_notification_test.py")
        else:
            logger.info("❌ Overlay is not connecting to the proxy bridge (port 8766)")
            logger.info("   Edit the overlay config.js to use ws://localhost:8766 for all connections")
        
        if connection_stats[8765] > 0:
            logger.info("✅ Overlay is correctly connecting to the DO button server (port 8765)")
        else:
            logger.info("❌ Overlay is not connecting to the DO button server (port 8765)")
        
        if connection_stats[8767] > 0:
            logger.info("✅ Overlay is connecting to the backend server (port 8767)")
        
        if not any(connection_stats.values()):
            logger.info("⚠️ No connections detected - overlay might not be running")
            logger.info("   Start the overlay with: cd overlay && npm run tauri dev")

if __name__ == "__main__":
    asyncio.run(main())