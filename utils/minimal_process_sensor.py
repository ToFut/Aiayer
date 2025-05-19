#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

async def send_process_data():
    """Collect and send process data to the bridge server"""
    uri = "ws://localhost:8765"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to bridge server at {uri}")
                
                # Process initial welcome message
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received from server: {data.get('type')}")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "process_sensor",
                        "version": "0.1.0"
                    }
                }))
                
                # Main data collection loop
                while True:
                    try:
                        # Collect process data
                        processes = []
                        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                            try:
                                # Get process info
                                proc_info = proc.info
                                memory_mb = proc_info['memory_info'].rss / (1024 * 1024) if proc_info['memory_info'] else 0
                                
                                processes.append({
                                    "pid": proc_info['pid'],
                                    "name": proc_info['name'],
                                    "cpu": proc_info['cpu_percent'],
                                    "memory": round(memory_mb, 1)
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                pass
                        
                        # Sort by CPU usage (descending)
                        processes.sort(key=lambda x: x['cpu'], reverse=True)
                        # Take top 10 processes
                        top_processes = processes[:10]
                        
                        # Send to bridge server
                        await websocket.send(json.dumps({
                            "type": "process_data",
                            "payload": top_processes,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Wait before next collection
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        logger.error(f"Error in data collection: {e}")
                        await asyncio.sleep(5)
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/process_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info("Starting minimal process sensor...")
    asyncio.run(send_process_data())
